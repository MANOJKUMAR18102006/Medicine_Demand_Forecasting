"""
Exchange Service: Manages Peer-to-Peer Medical Shop Stock Exchange & Request Lifecycle.
Protects supplying shop's 7-day forecast demand, safety stock, and active reservations.
"""

import math
import uuid
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

from backend.database import get_db
from ml.predict import forecast_demand


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 1)


class ExchangeService:
    """Orchestrates peer-to-peer medicine exchanges with mathematical surplus safeguards."""

    @classmethod
    def find_surplus_shops(
        cls,
        requesting_shop_id: str,
        medicine_name: str,
    ) -> List[Dict[str, Any]]:
        """
        Find registered medical shops with legitimate transferable surplus.
        Protects supplying shop's own 7-day forecast demand, safety buffer,
        and existing pending reservations before classifying stock as surplus.
        """
        med_clean = medicine_name.strip()

        # 1. Compute 7-day ML forecasted demand for this drug
        try:
            f_res = forecast_demand(med_clean, 7)
            projected_7d = int(f_res["total_predicted_demand"])
        except Exception:
            projected_7d = 200

        with get_db() as conn:
            cursor = conn.cursor()

            # Retrieve requesting shop's location for reliable distance calculation
            cursor.execute(
                "SELECT latitude, longitude, city FROM medical_shops WHERE id = ?;",
                (requesting_shop_id,),
            )
            req_shop = cursor.fetchone()
            req_lat = req_shop["latitude"] if req_shop else None
            req_lon = req_shop["longitude"] if req_shop else None

            # Retrieve all OTHER active shops holding this medicine
            cursor.execute(
                """
                SELECT 
                    s.id AS shop_id,
                    s.shop_name,
                    s.owner_name,
                    s.phone_number,
                    s.address,
                    s.city,
                    s.latitude,
                    s.longitude,
                    m.id AS medicine_id,
                    m.medicine_name,
                    m.category,
                    m.unit_of_measurement,
                    m.unit_price,
                    COALESCE(i.current_stock, 0) AS current_stock,
                    COALESCE(i.safety_stock, 20) AS safety_stock,
                    COALESCE(i.reserved_stock, 0) AS reserved_stock,
                    i.expiry_date
                FROM medical_shops s
                JOIN medicines m ON s.id = m.shop_id
                JOIN inventories i ON m.id = i.medicine_id
                WHERE s.id != ?
                  AND s.account_status = 'active'
                  AND COALESCE(m.is_archived, 0) = 0
                  AND m.medicine_name = ? COLLATE NOCASE;
                """,
                (requesting_shop_id, med_clean),
            )
            candidates = [dict(r) for r in cursor.fetchall()]

        results = []
        for c in candidates:
            curr_stock = int(c["current_stock"])
            safe_stock = int(c["safety_stock"])
            res_stock = int(c["reserved_stock"])

            # Surplus formula: Available Stock - Safety Buffer - 7-day Demand - Existing Reservations
            surplus = curr_stock - safe_stock - projected_7d - res_stock

            if surplus > 0:
                dist = None
                if req_lat and req_lon and c.get("latitude") and c.get("longitude"):
                    dist = haversine_distance(req_lat, req_lon, c["latitude"], c["longitude"])

                results.append({
                    "shop_id": c["shop_id"],
                    "shop_name": c["shop_name"],
                    "owner_name": c["owner_name"],
                    "phone_number": c["phone_number"],
                    "address": c["address"],
                    "city": c.get("city") or "Local Area",
                    "distance_km": dist,
                    "medicine_name": c["medicine_name"],
                    "category": c["category"],
                    "current_stock": curr_stock,
                    "safety_stock": safe_stock,
                    "projected_7d_demand": projected_7d,
                    "reserved_stock": res_stock,
                    "available_surplus": surplus,
                    "unit_of_measurement": c["unit_of_measurement"],
                    "unit_price": float(c["unit_price"]),
                    "expiry_date": c["expiry_date"],
                })

        # Sort by distance if known, else by highest surplus
        results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 99999, -x["available_surplus"]))
        return results

    @classmethod
    def create_exchange_request(
        cls,
        requesting_shop_id: str,
        supplying_shop_id: str,
        medicine_name: str,
        quantity: int,
        urgency: str = "Standard",
        request_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a formal stock exchange request to another shop."""
        if requesting_shop_id == supplying_shop_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request an exchange from your own shop.",
            )

        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested exchange quantity must be greater than zero.",
            )

        med_clean = medicine_name.strip()

        # Check supplying shop has sufficient surplus
        surplus_shops = cls.find_surplus_shops(requesting_shop_id, med_clean)
        target = next((s for s in surplus_shops if s["shop_id"] == supplying_shop_id), None)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target shop does not have transferable surplus for '{med_clean}'.",
            )

        if quantity > target["available_surplus"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({quantity}) exceeds available transferable surplus ({target['available_surplus']}).",
            )

        req_id = f"EXC-{uuid.uuid4().hex[:8].upper()}"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO exchange_requests (
                    id, requesting_shop_id, supplying_shop_id, medicine_name,
                    quantity, urgency, status, request_notes, unit_price
                ) VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?);
                """,
                (
                    req_id,
                    requesting_shop_id,
                    supplying_shop_id,
                    med_clean,
                    int(quantity),
                    urgency,
                    request_notes,
                    float(target["unit_price"]),
                ),
            )

        return cls.get_request_by_id(req_id)

    @classmethod
    def get_request_by_id(cls, request_id: str) -> Dict[str, Any]:
        """Fetch request details with shop names."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    r.id,
                    r.requesting_shop_id,
                    req.shop_name AS requesting_shop_name,
                    req.phone_number AS requesting_phone,
                    r.supplying_shop_id,
                    sup.shop_name AS supplying_shop_name,
                    sup.phone_number AS supplying_phone,
                    r.medicine_name,
                    r.quantity,
                    r.urgency,
                    r.status,
                    r.request_notes,
                    r.response_notes,
                    r.unit_price,
                    r.created_at,
                    r.updated_at
                FROM exchange_requests r
                JOIN medical_shops req ON r.requesting_shop_id = req.id
                JOIN medical_shops sup ON r.supplying_shop_id = sup.id
                WHERE r.id = ?;
                """,
                (request_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange request not found.",
            )
        return dict(row)

    @classmethod
    def get_incoming_requests(cls, shop_id: str) -> List[Dict[str, Any]]:
        """Retrieve exchange requests directed to this shop as the potential supplier."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    r.id,
                    r.requesting_shop_id,
                    req.shop_name AS requesting_shop_name,
                    req.phone_number AS requesting_phone,
                    r.supplying_shop_id,
                    sup.shop_name AS supplying_shop_name,
                    sup.phone_number AS supplying_phone,
                    r.medicine_name,
                    r.quantity,
                    r.urgency,
                    r.status,
                    r.request_notes,
                    r.response_notes,
                    r.unit_price,
                    r.created_at,
                    r.updated_at
                FROM exchange_requests r
                JOIN medical_shops req ON r.requesting_shop_id = req.id
                JOIN medical_shops sup ON r.supplying_shop_id = sup.id
                WHERE r.supplying_shop_id = ?
                ORDER BY r.created_at DESC;
                """,
                (shop_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def get_outgoing_requests(cls, shop_id: str) -> List[Dict[str, Any]]:
        """Retrieve exchange requests initiated by this shop."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    r.id,
                    r.requesting_shop_id,
                    req.shop_name AS requesting_shop_name,
                    req.phone_number AS requesting_phone,
                    r.supplying_shop_id,
                    sup.shop_name AS supplying_shop_name,
                    sup.phone_number AS supplying_phone,
                    r.medicine_name,
                    r.quantity,
                    r.urgency,
                    r.status,
                    r.request_notes,
                    r.response_notes,
                    r.unit_price,
                    r.created_at,
                    r.updated_at
                FROM exchange_requests r
                JOIN medical_shops req ON r.requesting_shop_id = req.id
                JOIN medical_shops sup ON r.supplying_shop_id = sup.id
                WHERE r.requesting_shop_id = ?
                ORDER BY r.created_at DESC;
                """,
                (shop_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def update_exchange_status(
        cls,
        shop_id: str,
        request_id: str,
        new_status: str,
        response_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transition exchange request through its lifecycle with atomic inventory synchronization.
        Valid statuses: Pending, Accepted, Reserved, Dispatched, Completed, Rejected, Cancelled.
        """
        valid_statuses = {"Pending", "Accepted", "Reserved", "Dispatched", "Completed", "Rejected", "Cancelled"}
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{new_status}'. Allowed: {', '.join(sorted(valid_statuses))}",
            )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exchange_requests WHERE id = ?;", (request_id,))
            req = cursor.fetchone()
            if not req:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exchange request not found.",
                )

            req_data = dict(req)
            current_status = req_data["status"]
            supplying_id = req_data["supplying_shop_id"]
            requesting_id = req_data["requesting_shop_id"]
            med_name = req_data["medicine_name"]
            qty = int(req_data["quantity"])

            # Authorization checks
            is_supplying = shop_id == supplying_id
            is_requesting = shop_id == requesting_id

            if not (is_supplying or is_requesting):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized: You are neither the requester nor supplier for this exchange.",
                )

            # Restrict actions based on role
            if new_status in ("Accepted", "Reserved", "Dispatched", "Rejected") and not is_supplying:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Only the supplying shop can mark request as '{new_status}'.",
                )

            if new_status == "Completed" and not is_requesting:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the requesting shop can confirm receipt and complete the exchange.",
                )

            if new_status == "Cancelled":
                if current_status in ("Dispatched", "Completed"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot cancel exchange once dispatched or completed.",
                    )

            # Supplying shop's medicine & inventory lookup
            cursor.execute(
                """
                SELECT m.id AS medicine_id, i.current_stock, i.reserved_stock
                FROM medicines m
                JOIN inventories i ON m.id = i.medicine_id
                WHERE m.shop_id = ? AND m.medicine_name = ? COLLATE NOCASE;
                """,
                (supplying_id, med_name),
            )
            sup_inv = cursor.fetchone()

            # Handle state transitions
            if new_status in ("Accepted", "Reserved"):
                if current_status not in ("Pending",):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot transition to '{new_status}' from '{current_status}'.",
                    )
                if not sup_inv or (sup_inv["current_stock"] - sup_inv["reserved_stock"]) < qty:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Supplying shop no longer has sufficient unreserved stock to fulfill this exchange.",
                    )

                # Reserve stock in supplying shop
                cursor.execute(
                    "UPDATE inventories SET reserved_stock = reserved_stock + ? WHERE medicine_id = ?;",
                    (qty, sup_inv["medicine_id"]),
                )
                # Audit log
                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (id, shop_id, medicine_id, transaction_type, quantity, balance_after, reference_id, notes)
                    VALUES (?, ?, ?, 'reservation', ?, ?, ?, 'Stock reserved for exchange request');
                    """,
                    (str(uuid.uuid4()), supplying_id, sup_inv["medicine_id"], qty, sup_inv["current_stock"], request_id),
                )

            elif new_status == "Dispatched":
                if current_status not in ("Accepted", "Reserved"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Request must be Accepted or Reserved before it can be Dispatched.",
                    )

            elif new_status == "Completed":
                if current_status not in ("Dispatched", "Accepted", "Reserved"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot complete exchange from status '{current_status}'.",
                    )

                # 1. Deduct from supplying shop (release reserved & reduce current_stock)
                new_sup_curr = max(0, sup_inv["current_stock"] - qty)
                new_sup_res = max(0, sup_inv["reserved_stock"] - qty)
                cursor.execute(
                    """
                    UPDATE inventories 
                    SET current_stock = ?, reserved_stock = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE medicine_id = ?;
                    """,
                    (new_sup_curr, new_sup_res, sup_inv["medicine_id"]),
                )
                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (id, shop_id, medicine_id, transaction_type, quantity, balance_after, reference_id, notes)
                    VALUES (?, ?, ?, 'exchange_out', ?, ?, ?, 'Stock transferred to peer shop via exchange');
                    """,
                    (str(uuid.uuid4()), supplying_id, sup_inv["medicine_id"], -qty, new_sup_curr, request_id),
                )

                # 2. Add to requesting shop's inventory
                cursor.execute(
                    """
                    SELECT m.id AS medicine_id, i.current_stock
                    FROM medicines m
                    JOIN inventories i ON m.id = i.medicine_id
                    WHERE m.shop_id = ? AND m.medicine_name = ? COLLATE NOCASE;
                    """,
                    (requesting_id, med_name),
                )
                req_inv = cursor.fetchone()

                if req_inv:
                    new_req_curr = req_inv["current_stock"] + qty
                    cursor.execute(
                        "UPDATE inventories SET current_stock = ?, last_updated = CURRENT_TIMESTAMP WHERE medicine_id = ?;",
                        (new_req_curr, req_inv["medicine_id"]),
                    )
                    req_med_id = req_inv["medicine_id"]
                else:
                    # Create medicine in requesting shop's catalog
                    req_med_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO medicines (id, shop_id, medicine_name, category, unit_of_measurement, unit_price)
                        VALUES (?, ?, ?, 'General', 'units', ?);
                        """,
                        (req_med_id, requesting_id, med_name, float(req_data["unit_price"])),
                    )
                    new_req_curr = qty
                    cursor.execute(
                        """
                        INSERT INTO inventories (id, shop_id, medicine_id, current_stock, safety_stock, reorder_threshold)
                        VALUES (?, ?, ?, ?, 20, 50);
                        """,
                        (str(uuid.uuid4()), requesting_id, req_med_id, new_req_curr),
                    )

                cursor.execute(
                    """
                    INSERT INTO inventory_transactions (id, shop_id, medicine_id, transaction_type, quantity, balance_after, reference_id, notes)
                    VALUES (?, ?, ?, 'exchange_in', ?, ?, ?, 'Stock received from peer shop via exchange');
                    """,
                    (str(uuid.uuid4()), requesting_id, req_med_id, qty, new_req_curr, request_id),
                )

            elif new_status in ("Rejected", "Cancelled"):
                # If reservation was active, release reserved stock
                if current_status in ("Accepted", "Reserved"):
                    cursor.execute(
                        "UPDATE inventories SET reserved_stock = MAX(0, reserved_stock - ?) WHERE medicine_id = ?;",
                        (qty, sup_inv["medicine_id"]),
                    )
                    cursor.execute(
                        """
                        INSERT INTO inventory_transactions (id, shop_id, medicine_id, transaction_type, quantity, balance_after, reference_id, notes)
                        VALUES (?, ?, ?, 'reservation_release', ?, ?, ?, 'Reservation released upon rejection/cancellation');
                        """,
                        (str(uuid.uuid4()), supplying_id, sup_inv["medicine_id"], -qty, sup_inv["current_stock"], request_id),
                    )

            # Update request status
            cursor.execute(
                """
                UPDATE exchange_requests
                SET status = ?, response_notes = COALESCE(?, response_notes), updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (new_status, response_notes, request_id),
            )

        return cls.get_request_by_id(request_id)

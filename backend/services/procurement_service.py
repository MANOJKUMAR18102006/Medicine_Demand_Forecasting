"""
Procurement Service: Manages Authorized Supplier Marketplace, Purchase Orders & Stock Intake.
Ensures zero duplicate stock additions and authentic supplier transactions.
"""

import uuid
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

from backend.database import get_db


class ProcurementService:
    """Manages verified pharmaceutical suppliers, catalog searches, and purchase order workflow."""

    @classmethod
    def list_suppliers(cls) -> List[Dict[str, Any]]:
        """Return list of authorized pharmaceutical distributors."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, supplier_name, contact_person, email, phone_number,
                       address, license_number, rating, is_verified, created_at
                FROM suppliers
                ORDER BY rating DESC, supplier_name ASC;
                """
            )
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def search_products(
        cls,
        query: Optional[str] = None,
        category: Optional[str] = None,
        supplier_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search available medicines across authorized supplier catalogs."""
        clauses = ["sp.is_active = 1", "sp.available_quantity > 0"]
        params = []

        if query and query.strip():
            q = f"%{query.strip()}%"
            clauses.append("(sp.medicine_name LIKE ? OR sp.manufacturer LIKE ? OR sp.dosage_form LIKE ?)")
            params.extend([q, q, q])

        if category and category.strip() and category != "All":
            clauses.append("sp.category LIKE ?")
            params.append(f"%{category.strip()}%")

        if supplier_id and supplier_id.strip():
            clauses.append("sp.supplier_id = ?")
            params.append(supplier_id.strip())

        sql = f"""
            SELECT 
                sp.id,
                sp.supplier_id,
                s.supplier_name,
                s.rating AS supplier_rating,
                sp.medicine_name,
                sp.category,
                sp.dosage_form,
                sp.strength,
                sp.manufacturer,
                sp.unit_price,
                sp.available_quantity,
                sp.unit_of_measurement,
                sp.batch_number,
                sp.expiry_date,
                sp.estimated_delivery_days,
                sp.min_order_quantity,
                sp.is_active
            FROM supplier_products sp
            JOIN suppliers s ON sp.supplier_id = s.id
            WHERE {' AND '.join(clauses)}
            ORDER BY sp.medicine_name ASC, sp.unit_price ASC;
        """

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def create_purchase_order(
        cls,
        shop_id: str,
        supplier_id: str,
        items: List[Dict[str, Any]],
        delivery_address: str,
        payment_method: str = "Net 30 Invoice",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate supplier inventory in real-time, generate purchase order,
        and reserve supplier product stock.
        """
        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order must contain at least one item.",
            )

        order_id = f"PO-{uuid.uuid4().hex[:8].upper()}"
        tracking_num = f"TRK-{uuid.uuid4().hex[:10].upper()}"

        with get_db() as conn:
            cursor = conn.cursor()

            # Verify supplier exists
            cursor.execute("SELECT id, supplier_name FROM suppliers WHERE id = ?;", (supplier_id,))
            sup_row = cursor.fetchone()
            if not sup_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authorized supplier not found.",
                )

            # Validate each item against live supplier inventory
            validated_items = []
            total_amount = 0.0

            for itm in items:
                prod_id = itm["supplier_product_id"]
                req_qty = int(itm["quantity"])

                if req_qty <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Quantity must be greater than zero.",
                    )

                cursor.execute(
                    """
                    SELECT id, supplier_id, medicine_name, category, dosage_form, strength,
                           unit_price, available_quantity, min_order_quantity
                    FROM supplier_products
                    WHERE id = ? AND supplier_id = ? AND is_active = 1;
                    """,
                    (prod_id, supplier_id),
                )
                prod = cursor.fetchone()
                if not prod:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product '{prod_id}' is not offered by selected supplier.",
                    )

                prod_dict = dict(prod)
                if req_qty > prod_dict["available_quantity"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Supplier stock shortage for '{prod_dict['medicine_name']}': requested {req_qty}, only {prod_dict['available_quantity']} available.",
                    )

                min_moq = prod_dict.get("min_order_quantity") or 1
                if req_qty < min_moq:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Minimum order quantity for '{prod_dict['medicine_name']}' is {min_moq} units.",
                    )

                item_total = round(float(prod_dict["unit_price"]) * req_qty, 2)
                total_amount += item_total

                validated_items.append({
                    "id": str(uuid.uuid4()),
                    "supplier_product_id": prod_id,
                    "medicine_name": prod_dict["medicine_name"],
                    "category": prod_dict["category"],
                    "dosage_form": prod_dict["dosage_form"],
                    "strength": prod_dict["strength"],
                    "quantity": req_qty,
                    "unit_price": float(prod_dict["unit_price"]),
                    "total_price": item_total,
                })

            total_amount = round(total_amount, 2)

            # Create Purchase Order record
            cursor.execute(
                """
                INSERT INTO purchase_orders (
                    id, shop_id, supplier_id, status, total_amount, payment_method,
                    payment_status, delivery_address, tracking_number, notes, inventory_applied
                ) VALUES (?, ?, ?, 'Confirmed', ?, ?, 'Pending Invoice', ?, ?, ?, 0);
                """,
                (
                    order_id,
                    shop_id,
                    supplier_id,
                    total_amount,
                    payment_method,
                    delivery_address,
                    tracking_num,
                    notes,
                ),
            )

            # Insert line items & deduct from supplier product catalog
            for vi in validated_items:
                cursor.execute(
                    """
                    INSERT INTO purchase_order_items (
                        id, order_id, supplier_product_id, medicine_name, category,
                        dosage_form, strength, quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        vi["id"],
                        order_id,
                        vi["supplier_product_id"],
                        vi["medicine_name"],
                        vi["category"],
                        vi["dosage_form"],
                        vi["strength"],
                        vi["quantity"],
                        vi["unit_price"],
                        vi["total_price"],
                    ),
                )
                cursor.execute(
                    "UPDATE supplier_products SET available_quantity = available_quantity - ? WHERE id = ?;",
                    (vi["quantity"], vi["supplier_product_id"]),
                )

        return cls.get_order_by_id(shop_id, order_id)

    @classmethod
    def get_order_by_id(cls, shop_id: str, order_id: str) -> Dict[str, Any]:
        """Fetch purchase order details strictly verifying tenant ownership."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    po.id,
                    po.shop_id,
                    ms.shop_name,
                    po.supplier_id,
                    s.supplier_name,
                    po.status,
                    po.total_amount,
                    po.payment_method,
                    po.payment_status,
                    po.delivery_address,
                    po.tracking_number,
                    po.notes,
                    po.inventory_applied,
                    po.created_at,
                    po.updated_at
                FROM purchase_orders po
                JOIN medical_shops ms ON po.shop_id = ms.id
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.id = ? AND po.shop_id = ?;
                """,
                (order_id, shop_id),
            )
            po_row = cursor.fetchone()
            if not po_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found or unauthorized.",
                )

            order_data = dict(po_row)

            cursor.execute(
                """
                SELECT id, supplier_product_id, medicine_name, category, dosage_form,
                       strength, quantity, unit_price, total_price
                FROM purchase_order_items
                WHERE order_id = ?;
                """,
                (order_id,),
            )
            order_data["items"] = [dict(r) for r in cursor.fetchall()]

        return order_data

    @classmethod
    def get_shop_purchase_orders(cls, shop_id: str) -> List[Dict[str, Any]]:
        """Return list of purchase orders placed by this medical shop."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    po.id,
                    po.shop_id,
                    ms.shop_name,
                    po.supplier_id,
                    s.supplier_name,
                    po.status,
                    po.total_amount,
                    po.payment_method,
                    po.payment_status,
                    po.delivery_address,
                    po.tracking_number,
                    po.notes,
                    po.inventory_applied,
                    po.created_at,
                    po.updated_at
                FROM purchase_orders po
                JOIN medical_shops ms ON po.shop_id = ms.id
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.shop_id = ?
                ORDER BY po.created_at DESC;
                """,
                (shop_id,),
            )
            orders = [dict(r) for r in cursor.fetchall()]

            for o in orders:
                cursor.execute(
                    """
                    SELECT id, supplier_product_id, medicine_name, category, dosage_form,
                           strength, quantity, unit_price, total_price
                    FROM purchase_order_items
                    WHERE order_id = ?;
                    """,
                    (o["id"],),
                )
                o["items"] = [dict(r) for r in cursor.fetchall()]

        return orders

    @classmethod
    def update_order_status(
        cls,
        shop_id: str,
        order_id: str,
        new_status: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update purchase order status.
        When reaching 'Delivered', automatically synchronizes medicine inventory,
        preventing duplicate stock increments.
        """
        valid_statuses = {"Pending", "Confirmed", "Processing", "Dispatched", "Delivered", "Cancelled"}
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order status '{new_status}'. Allowed: {', '.join(sorted(valid_statuses))}",
            )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM purchase_orders WHERE id = ? AND shop_id = ?;", (order_id, shop_id))
            po_row = cursor.fetchone()
            if not po_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Purchase order not found or unauthorized.",
                )

            po = dict(po_row)
            prev_status = po["status"]
            inventory_applied = bool(po["inventory_applied"])

            if prev_status == "Delivered" and new_status == "Cancelled":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel an order that has already been delivered and stocked.",
                )

            # Fetch line items
            cursor.execute("SELECT * FROM purchase_order_items WHERE order_id = ?;", (order_id,))
            items = [dict(r) for r in cursor.fetchall()]

            # If marked Delivered and not yet applied, add stock to shop inventory
            if new_status == "Delivered" and not inventory_applied:
                for itm in items:
                    med_name = itm["medicine_name"]
                    qty = int(itm["quantity"])

                    # Check if medicine exists in shop catalog
                    cursor.execute(
                        """
                        SELECT m.id AS medicine_id, i.current_stock
                        FROM medicines m
                        JOIN inventories i ON m.id = i.medicine_id
                        WHERE m.shop_id = ? AND m.medicine_name = ? COLLATE NOCASE;
                        """,
                        (shop_id, med_name),
                    )
                    inv_row = cursor.fetchone()

                    if inv_row:
                        med_id = inv_row["medicine_id"]
                        new_curr = inv_row["current_stock"] + qty
                        cursor.execute(
                            "UPDATE inventories SET current_stock = ?, last_updated = CURRENT_TIMESTAMP WHERE medicine_id = ?;",
                            (new_curr, med_id),
                        )
                    else:
                        # Auto-create in shop catalog
                        med_id = str(uuid.uuid4())
                        cursor.execute(
                            """
                            INSERT INTO medicines (id, shop_id, medicine_name, category, dosage_form, strength, unit_of_measurement, unit_price)
                            VALUES (?, ?, ?, ?, ?, ?, 'units', ?);
                            """,
                            (
                                med_id,
                                shop_id,
                                med_name,
                                itm.get("category") or "General",
                                itm.get("dosage_form") or "Tablets",
                                itm.get("strength") or "Standard",
                                round(float(itm["unit_price"]) * 1.25, 2),  # Suggested retail price
                            ),
                        )
                        new_curr = qty
                        cursor.execute(
                            """
                            INSERT INTO inventories (id, shop_id, medicine_id, current_stock, safety_stock, reorder_threshold)
                            VALUES (?, ?, ?, ?, 20, 50);
                            """,
                            (str(uuid.uuid4()), shop_id, med_id, new_curr),
                        )

                    # Audit transaction log
                    cursor.execute(
                        """
                        INSERT INTO inventory_transactions (id, shop_id, medicine_id, transaction_type, quantity, balance_after, reference_id, notes)
                        VALUES (?, ?, ?, 'purchase', ?, ?, ?, 'Stock replenishment received from supplier purchase order');
                        """,
                        (str(uuid.uuid4()), shop_id, med_id, qty, new_curr, order_id),
                    )

                cursor.execute(
                    "UPDATE purchase_orders SET inventory_applied = 1 WHERE id = ?;",
                    (order_id,),
                )

            # If cancelled before delivery, return stock to supplier catalog
            elif new_status == "Cancelled" and prev_status != "Cancelled":
                for itm in items:
                    cursor.execute(
                        "UPDATE supplier_products SET available_quantity = available_quantity + ? WHERE id = ?;",
                        (itm["quantity"], itm["supplier_product_id"]),
                    )

            # Update purchase order status
            cursor.execute(
                """
                UPDATE purchase_orders
                SET status = ?, notes = COALESCE(?, notes), updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (new_status, notes, order_id),
            )

        return cls.get_order_by_id(shop_id, order_id)

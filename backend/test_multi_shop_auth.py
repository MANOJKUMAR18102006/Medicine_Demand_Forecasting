"""
Comprehensive Multi-Shop Authentication & Data Isolation Test Suite.
Validates:
1. Registration & password hashing (no plain-text passwords in DB)
2. Duplicate email rejection & input validations
3. Login & JWT authentication
4. Complete Multi-Tenant Shop Isolation (Shop A vs Shop B catalog & inventory)
5. Direct API ID-tampering denial
6. Multi-shop forecast history isolation
7. Profile update & password reset token flow
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database import init_db, get_db

client = TestClient(app)


def test_auth_and_multi_shop_isolation():
    print("\n" + "=" * 65)
    print("BEGINNING MULTI-SHOP AUTHENTICATION & DATA ISOLATION AUDIT")
    print("=" * 65)

    init_db()

    # Clear test records if present
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM medical_shops WHERE email IN ('shop_a@medtest.com', 'shop_b@medtest.com');")

    # -------------------------------------------------------------
    # 1. Registration Tests
    # -------------------------------------------------------------
    print("\n--- 1. REGISTRATION & PASSWORD HASHING ---")
    reg_payload_a = {
        "shop_name": "Apex City Pharmacy",
        "owner_name": "Dr. Alice Morgan",
        "email": "shop_a@medtest.com",
        "phone_number": "+1-555-0199",
        "address": "100 Healthcare Blvd, Suite 4",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    r = client.post("/api/auth/register", json=reg_payload_a)
    assert r.status_code == 201, f"Shop A registration failed: {r.text}"
    shop_a_data = r.json()
    assert shop_a_data["email"] == "shop_a@medtest.com"
    assert "password_hash" not in shop_a_data
    print("PASS: Shop A successfully registered with status 201.")

    # Verify password hash in DB is bcrypt and not plain-text
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM medical_shops WHERE email = 'shop_a@medtest.com';")
        db_row = cursor.fetchone()
        assert db_row is not None
        assert db_row["password_hash"].startswith("$2b$")
        assert "Password123!" not in db_row["password_hash"]
    print("PASS: Verified bcrypt password hashing in database; no plain text stored.")

    # Duplicate registration check
    r_dup = client.post("/api/auth/register", json=reg_payload_a)
    assert r_dup.status_code == 400
    assert "already registered" in r_dup.json()["detail"].lower()
    print("PASS: Duplicate email registration prevented with 400 Bad Request.")

    # Mismatched passwords check
    bad_pass_payload = dict(reg_payload_a, email="other@medtest.com", confirm_password="WrongConfirm!")
    r_bad = client.post("/api/auth/register", json=bad_pass_payload)
    assert r_bad.status_code == 422
    print("PASS: Mismatched password and confirm_password rejected with 422.")

    # Register Shop B
    reg_payload_b = {
        "shop_name": "Green Cross Chemist",
        "owner_name": "Mr. Bob Sanders",
        "email": "shop_b@medtest.com",
        "phone_number": "+1-555-0288",
        "address": "450 Market Street, Bay 2",
        "password": "Secret456Password!",
        "confirm_password": "Secret456Password!",
    }
    r_b = client.post("/api/auth/register", json=reg_payload_b)
    assert r_b.status_code == 201
    shop_b_data = r_b.json()
    print("PASS: Shop B successfully registered.")

    # -------------------------------------------------------------
    # 2. Login & JWT Verification
    # -------------------------------------------------------------
    print("\n--- 2. LOGIN & JWT AUTHENTICATION ---")
    # Invalid password
    r_login_fail = client.post("/api/auth/login", json={"email": "shop_a@medtest.com", "password": "WrongPassword"})
    assert r_login_fail.status_code == 401
    print("PASS: Invalid credentials rejected with 401 Unauthorized.")

    # Successful login for Shop A
    r_login_a = client.post("/api/auth/login", json={"email": "shop_a@medtest.com", "password": "Password123!"})
    assert r_login_a.status_code == 200
    auth_a = r_login_a.json()
    token_a = auth_a["access_token"]
    assert token_a is not None
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print("PASS: Shop A authenticated and received valid JWT token.")

    # Successful login for Shop B
    r_login_b = client.post("/api/auth/login", json={"email": "shop_b@medtest.com", "password": "Secret456Password!"})
    assert r_login_b.status_code == 200
    auth_b = r_login_b.json()
    token_b = auth_b["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print("PASS: Shop B authenticated and received valid JWT token.")

    # Profile verification
    r_me_a = client.get("/api/auth/me", headers=headers_a)
    assert r_me_a.status_code == 200 and r_me_a.json()["shop_name"] == "Apex City Pharmacy"

    r_me_b = client.get("/api/auth/me", headers=headers_b)
    assert r_me_b.status_code == 200 and r_me_b.json()["shop_name"] == "Green Cross Chemist"
    print("PASS: Server-side identity verified via GET /api/auth/me for both shops.")

    # -------------------------------------------------------------
    # 3. Multi-Tenant Shop Isolation Tests (Highest Priority)
    # -------------------------------------------------------------
    print("\n--- 3. MULTI-SHOP DATA ISOLATION AUDIT ---")
    # Shop A starts empty
    r_meds_a_init = client.get("/api/medicines", headers=headers_a)
    assert r_meds_a_init.status_code == 200
    assert r_meds_a_init.json() == [], "New shop should start with 0 medicines"

    # Shop A creates exclusive drug: "Paracetamol-Apex"
    med_a_payload = {
        "medicine_name": "Paracetamol-Apex",
        "category": "Analgesic",
        "unit_of_measurement": "tablets",
        "unit_price": 6.5,
        "initial_stock": 1200,
        "safety_stock": 100,
        "reorder_threshold": 250,
    }
    r_add_a = client.post("/api/medicines", json=med_a_payload, headers=headers_a)
    assert r_add_a.status_code == 201
    item_a = r_add_a.json()
    id_a = item_a["id"]
    print("PASS: Shop A created medicine 'Paracetamol-Apex' (ID: %s)." % id_a)

    # Shop B creates exclusive drug: "Insulin-GreenCross"
    med_b_payload = {
        "medicine_name": "Insulin-GreenCross",
        "category": "Antidiabetic",
        "unit_of_measurement": "vials",
        "unit_price": 55.0,
        "initial_stock": 75,
        "safety_stock": 30,
        "reorder_threshold": 60,
    }
    r_add_b = client.post("/api/medicines", json=med_b_payload, headers=headers_b)
    assert r_add_b.status_code == 201
    item_b = r_add_b.json()
    id_b = item_b["id"]
    print("PASS: Shop B created medicine 'Insulin-GreenCross' (ID: %s)." % id_b)

    # Verify Shop A sees ONLY Shop A's medicine
    r_catalog_a = client.get("/api/medicines", headers=headers_a)
    assert r_catalog_a.json() == ["Paracetamol-Apex"]
    assert "Insulin-GreenCross" not in r_catalog_a.json()
    print("PASS: Shop A catalog contains ONLY Shop A medicines.")

    # Verify Shop B sees ONLY Shop B's medicine
    r_catalog_b = client.get("/api/medicines", headers=headers_b)
    assert r_catalog_b.json() == ["Insulin-GreenCross"]
    assert "Paracetamol-Apex" not in r_catalog_b.json()
    print("PASS: Shop B catalog contains ONLY Shop B medicines.")

    # Direct ID Tampering Attack: Shop B tries to modify Shop A's inventory record
    r_tamper = client.post(
        f"/api/inventory/{id_a}",
        json={"current_stock": 0},
        headers=headers_b,
    )
    assert r_tamper.status_code == 404, "Cross-tenant access was not blocked!"
    print("PASS: Shop B attempting to alter Shop A's medicine by ID was denied (404 Not Found).")

    # Verify Shop A's stock was untouched
    r_verify_a = client.get("/api/medicines/items", headers=headers_a)
    assert r_verify_a.json()[0]["current_stock"] == 1200
    print("PASS: Verified Shop A's stock remained protected and unmodified.")

    # -------------------------------------------------------------
    # 4. Forecast History & Analytics Isolation
    # -------------------------------------------------------------
    print("\n--- 4. FORECAST & ANALYTICS ISOLATION ---")
    # Shop A generates forecast for its drug
    r_fc_a = client.post(
        "/api/forecast",
        json={"medicine": "Paracetamol-Apex", "days": 7},
        headers=headers_a,
    )
    assert r_fc_a.status_code == 200
    data_fc_a = r_fc_a.json()
    assert data_fc_a["total_predicted_demand"] > 0
    print(f"PASS: Generated 7-day XGBoost forecast for Shop A (Total: {data_fc_a['total_predicted_demand']} units).")

    # Check forecast history
    r_hist_a = client.get("/api/forecasts/history", headers=headers_a)
    assert len(r_hist_a.json()) >= 1
    assert r_hist_a.json()[0]["medicine_name"] == "Paracetamol-Apex"

    # Shop B should have zero forecast history
    r_hist_b = client.get("/api/forecasts/history", headers=headers_b)
    assert len(r_hist_b.json()) == 0
    print("PASS: Forecast execution history is strictly tenant-isolated.")

    # Check isolated analytics summary
    r_sum_a = client.get("/api/analytics/summary", headers=headers_a)
    assert r_sum_a.status_code == 200
    sum_a = r_sum_a.json()
    assert sum_a["total_medicines"] == 1
    assert sum_a["top_medicines"][0]["medicine"] == "Paracetamol-Apex"

    r_sum_b = client.get("/api/analytics/summary", headers=headers_b)
    assert r_sum_b.status_code == 200
    sum_b = r_sum_b.json()
    assert sum_b["total_medicines"] == 1
    assert sum_b["top_medicines"][0]["medicine"] == "Insulin-GreenCross"
    print("PASS: Analytics summary and KPIs are strictly isolated per medical shop.")

    # -------------------------------------------------------------
    # 5. Profile Update & Password Recovery Flow
    # -------------------------------------------------------------
    print("\n--- 5. PROFILE UPDATE & PASSWORD RECOVERY ---")
    # Update profile
    r_prof = client.put(
        "/api/auth/profile",
        json={"address": "999 Innovation Parkway"},
        headers=headers_a,
    )
    assert r_prof.status_code == 200 and r_prof.json()["address"] == "999 Innovation Parkway"
    print("PASS: Shop profile updated successfully.")

    # Forgot password request
    r_forgot = client.post("/api/auth/forgot-password", json={"email": "shop_a@medtest.com"})
    assert r_forgot.status_code == 200
    reset_token = r_forgot.json()["reset_token"]
    assert reset_token is not None

    # Reset password with token
    r_reset = client.post(
        "/api/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewBrandPassword999!",
            "confirm_password": "NewBrandPassword999!",
        },
    )
    assert r_reset.status_code == 200

    # Old password should now fail
    r_old_fail = client.post("/api/auth/login", json={"email": "shop_a@medtest.com", "password": "Password123!"})
    assert r_old_fail.status_code == 401

    # New password should succeed
    r_new_ok = client.post("/api/auth/login", json={"email": "shop_a@medtest.com", "password": "NewBrandPassword999!"})
    assert r_new_ok.status_code == 200
    print("PASS: Secure password reset flow verified; new password successfully activated.")

    print("\n" + "=" * 65)
    print("ALL MULTI-SHOP AUTHENTICATION & DATA ISOLATION TESTS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    test_auth_and_multi_shop_isolation()

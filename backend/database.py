"""
Database Connection & Persistence Layer for Multi-Shop MedDemand.

Uses SQLite with thread-safe connection pooling, foreign keys enabled,
and parameterized queries for robust multi-tenant data isolation.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.environ.get("MEDDEMAND_DB_PATH", os.path.join(PROJECT_ROOT, "backend", "meddemand.db"))


def get_db_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys and dict-like row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for acquiring and closing database connections safely."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables, indexes, and constraints if they do not exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Medical Shop / User Model
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medical_shops (
                id TEXT PRIMARY KEY,
                shop_name TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                phone_number TEXT NOT NULL,
                address TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                account_status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Medicine Model (Isolated per shop)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id TEXT PRIMARY KEY,
                shop_id TEXT NOT NULL,
                medicine_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_of_measurement TEXT NOT NULL DEFAULT 'units',
                unit_price REAL NOT NULL DEFAULT 10.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shop_id) REFERENCES medical_shops (id) ON DELETE CASCADE,
                UNIQUE(shop_id, medicine_name COLLATE NOCASE)
            );
        """)

        # 3. Inventory Model (1-to-1 with medicine per shop)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventories (
                id TEXT PRIMARY KEY,
                shop_id TEXT NOT NULL,
                medicine_id TEXT NOT NULL UNIQUE,
                current_stock INTEGER NOT NULL DEFAULT 0,
                safety_stock INTEGER NOT NULL DEFAULT 20,
                reorder_threshold INTEGER NOT NULL DEFAULT 50,
                expiry_date TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shop_id) REFERENCES medical_shops (id) ON DELETE CASCADE,
                FOREIGN KEY (medicine_id) REFERENCES medicines (id) ON DELETE CASCADE
            );
        """)

        # 4. Forecast History Model (Isolated per shop)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_history (
                id TEXT PRIMARY KEY,
                shop_id TEXT NOT NULL,
                medicine_id TEXT,
                medicine_name TEXT NOT NULL,
                forecast_horizon INTEGER NOT NULL,
                predicted_demand INTEGER NOT NULL,
                forecast_generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_identifier TEXT NOT NULL DEFAULT 'XGBoost Regressor',
                details_json TEXT,
                FOREIGN KEY (shop_id) REFERENCES medical_shops (id) ON DELETE CASCADE
            );
        """)

        # 5. Password Reset Tokens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                shop_id TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shop_id) REFERENCES medical_shops (id) ON DELETE CASCADE
            );
        """)

        # Indexes for fast lookup & tenant isolation
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shops_email ON medical_shops(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_medicines_shop ON medicines(shop_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventories_shop ON inventories(shop_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_shop ON forecast_history(shop_id);")


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)

import json
import sqlite3

from app.config import DB_PATH, JSON_PATH


def get_db_connection():
    """Create a SQLite connection and return a row-friendly cursor."""
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the vehicle catalog database and seed it from JSON if empty."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            variants TEXT NOT NULL,
            fuel TEXT NOT NULL,
            transmission TEXT NOT NULL,
            body TEXT NOT NULL,
            premium_brand INTEGER NOT NULL DEFAULT 0,
            UNIQUE(brand, model)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            variant TEXT NOT NULL,
            fuel TEXT NOT NULL,
            transmission TEXT NOT NULL,
            body TEXT NOT NULL,
            owner_type TEXT NOT NULL,
            City TEXT NOT NULL,
            state TEXT NOT NULL,
            km REAL NOT NULL,
            car_age INTEGER NOT NULL,
            premium_brand INTEGER NOT NULL,
            predicted_price REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        )
        """
    )

    connection.commit()

    cursor.execute("SELECT COUNT(*) AS count FROM vehicles")
    row = cursor.fetchone()
    if row is None or row[0] == 0:
        with open(JSON_PATH, encoding="utf-8") as json_file:
            catalog = json.load(json_file)

        for brand, models in catalog.items():
            for model, details in models.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO vehicles (brand, model, variants, fuel, transmission, body, premium_brand) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        brand,
                        model,
                        json.dumps(details.get("variants", []), ensure_ascii=False),
                        json.dumps(details.get("fuel", []), ensure_ascii=False),
                        json.dumps(details.get("transmission", []), ensure_ascii=False),
                        details.get("body", ""),
                        int(details.get("premium_brand", 0)),
                    ),
                )
        connection.commit()

    return connection


def list_brands(connection):
    """Return a sorted list of brands from the vehicle catalog."""
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT brand FROM vehicles ORDER BY LOWER(brand)")
    return [row["brand"] for row in cursor.fetchall()]


def list_models(connection, brand):
    """Return models for a brand, using case-insensitive lookup."""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT model FROM vehicles WHERE LOWER(brand)=LOWER(?) ORDER BY LOWER(model)",
        (brand,),
    )
    return [row["model"] for row in cursor.fetchall()]


def search_brands(connection, query=None):
    """Return brands matching a search query."""
    cursor = connection.cursor()
    if query:
        like_query = f"%{query.lower()}%"
        cursor.execute(
            "SELECT DISTINCT brand FROM vehicles WHERE LOWER(brand) LIKE ? ORDER BY LOWER(brand)",
            (like_query,),
        )
    else:
        cursor.execute("SELECT DISTINCT brand FROM vehicles ORDER BY LOWER(brand)")
    return [row["brand"] for row in cursor.fetchall()]


def search_models(connection, brand, query=None):
    """Return models for a brand matching a search query."""
    cursor = connection.cursor()
    if query:
        like_query = f"%{query.lower()}%"
        cursor.execute(
            "SELECT model FROM vehicles WHERE LOWER(brand)=LOWER(?) AND LOWER(model) LIKE ? ORDER BY LOWER(model)",
            (brand, like_query),
        )
    else:
        cursor.execute(
            "SELECT model FROM vehicles WHERE LOWER(brand)=LOWER(?) ORDER BY LOWER(model)",
            (brand,),
        )
    return [row["model"] for row in cursor.fetchall()]


def list_vehicles(connection, search=None, limit=50):
    """Return vehicles by optional brand/model search query."""
    cursor = connection.cursor()
    if search:
        like_query = f"%{search.lower()}%"
        cursor.execute(
            "SELECT brand, model FROM vehicles WHERE LOWER(brand) LIKE ? OR LOWER(model) LIKE ? ORDER BY LOWER(brand), LOWER(model) LIMIT ?",
            (like_query, like_query, limit),
        )
    else:
        cursor.execute(
            "SELECT brand, model FROM vehicles ORDER BY LOWER(brand), LOWER(model) LIMIT ?",
            (limit,),
        )
    return [{"brand": row["brand"], "model": row["model"]} for row in cursor.fetchall()]


def count_brands(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(DISTINCT brand) AS count FROM vehicles")
    return cursor.fetchone()["count"]


def count_models(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM vehicles")
    return cursor.fetchone()["count"]


def count_predictions(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM prediction_history")
    row = cursor.fetchone()
    return row["count"] if row is not None else 0


def get_vehicle_details(connection, brand, model):
    """Return vehicle metadata for the selected brand and model."""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT variants, fuel, transmission, body, premium_brand FROM vehicles WHERE LOWER(brand)=LOWER(?) AND LOWER(model)=LOWER(?)",
        (brand, model),
    )
    row = cursor.fetchone()
    if row is None:
        return {}

    return {
        "variants": json.loads(row["variants"]),
        "fuel": json.loads(row["fuel"]),
        "transmission": json.loads(row["transmission"]),
        "body": row["body"],
        "premium_brand": "Yes" if row["premium_brand"] == 1 else "No",
    }


def record_prediction(connection, payload, predicted_price):
    """Store a prediction entry in the persistent history table."""
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO prediction_history (brand, model, variant, fuel, transmission, body, owner_type, City, state, km, car_age, premium_brand, predicted_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            payload["oem"],
            payload["model"],
            payload["variant"],
            payload["fuel"],
            payload["transmission"],
            payload["body"],
            payload["owner_type"],
            payload["City"],
            payload["state"],
            payload["km"],
            payload["car_age"],
            payload["premium_brand"],
            float(predicted_price),
        ),
    )
    connection.commit()
    return cursor.lastrowid


def list_history(connection, limit=20):
    """Return recent prediction history entries."""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, brand, model, variant, fuel, transmission, body, owner_type, City, state, km, car_age, premium_brand, predicted_price, created_at FROM prediction_history ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "brand": row["brand"],
            "model": row["model"],
            "variant": row["variant"],
            "fuel": row["fuel"],
            "transmission": row["transmission"],
            "body": row["body"],
            "owner_type": row["owner_type"],
            "City": row["City"],
            "state": row["state"],
            "km": row["km"],
            "car_age": row["car_age"],
            "premium_brand": row["premium_brand"],
            "predicted_price": row["predicted_price"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def clear_history(connection):
    """Delete all prediction history records."""
    cursor = connection.cursor()
    cursor.execute("DELETE FROM prediction_history")
    connection.commit()

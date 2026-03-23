import sqlite3


def run_migration():
    conn = sqlite3.connect("diesel_erp.db")
    cursor = conn.cursor()

    # Check if columns already exist to make script idempotent
    cursor.execute("PRAGMA table_info(trips)")
    columns = [row[1] for row in cursor.fetchall()]

    updates = []
    if "material" not in columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN material VARCHAR")
        updates.append("material")
    if "qty_mt" not in columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN qty_mt FLOAT")
        updates.append("qty_mt")
    if "driver_name" not in columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN driver_name VARCHAR")
        updates.append("driver_name")
    if "driver_number" not in columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN driver_number VARCHAR")
        updates.append("driver_number")

    conn.commit()
    conn.close()
    print("Migration successful. Added columns:", updates)


if __name__ == "__main__":
    run_migration()

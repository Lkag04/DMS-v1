import sqlite3


def migrate():
    conn = sqlite3.connect("diesel_erp.db")
    c = conn.cursor()

    print("Migrating DieselTokens database schema...")
    try:
        c.execute(
            "ALTER TABLE diesel_tokens ADD COLUMN remaining_value FLOAT DEFAULT 0.0"
        )
        # Initialize remaining_value with original value for existing active tokens
        c.execute(
            "UPDATE diesel_tokens SET remaining_value = value WHERE status = 'issued'"
        )
        print(" Added remaining_value")
    except sqlite3.OperationalError:
        print(" remaining_value already exists")

    try:
        c.execute(
            "ALTER TABLE diesel_tokens ADD COLUMN overdraft_amount FLOAT DEFAULT 0.0"
        )
        print(" Added overdraft_amount")
    except sqlite3.OperationalError:
        print(" overdraft_amount already exists")

    try:
        c.execute(
            "ALTER TABLE diesel_tokens ADD COLUMN overdraft_status VARCHAR DEFAULT 'none'"
        )
        print(" Added overdraft_status")
    except sqlite3.OperationalError:
        print(" overdraft_status already exists")

    print("\nMigrating Existing Users Roles...")
    c.execute("UPDATE users SET role = 'master_admin' WHERE role = 'admin'")
    c.execute("UPDATE users SET role = 'factory_ops' WHERE role = 'factory'")
    c.execute("UPDATE users SET role = 'pump_ops' WHERE role = 'pump'")

    conn.commit()
    conn.close()
    print(" Migration completed successfully.")


if __name__ == "__main__":
    migrate()

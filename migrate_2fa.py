import sqlite3

def migrate():
    print("Connecting to database...")
    conn = sqlite3.connect("diesel_erp.db")
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR;")
        print("Added email column to users table.")
    except sqlite3.OperationalError as e:
        print(f"Column email might already exist: {e}")

    try:
        cursor.execute("CREATE UNIQUE INDEX idx_users_email ON users(email);")
        print("Created unique index on email")
    except Exception as e:
        print(f"Index creation error: {e}")

    try:
        cursor.execute("UPDATE users SET email = username || '@system.local' WHERE email IS NULL;")
        print("Populated dummy emails for existing system users.")
    except Exception as e:
        print(f"Failed to populate default emails: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()

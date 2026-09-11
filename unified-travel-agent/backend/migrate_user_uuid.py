"""
One-off migration: switch user_id everywhere from the raw username (a plain,
human-readable string used as both the users table's primary key and the
value embedded in every JWT) to a stable, opaque UUID.

Runs as a single transaction - if anything fails partway, everything rolls
back and the database is left exactly as it was. Backfills existing rows
before dropping anything, and verifies row counts match before committing.

Run once, manually:
    venv/Scripts/python migrate_user_uuid.py
"""

from database import get_db_connection

DEPENDENT_TABLES = ["sessions", "chat_messages", "bookings", "itineraries"]


def main() -> None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            print("1. Adding user_uuid to users (backfilled for existing accounts)...")
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_uuid UUID "
                "NOT NULL DEFAULT gen_random_uuid() UNIQUE"
            )
            cur.execute("SELECT count(*) AS n FROM users")
            user_count = cur.fetchone()["n"]
            print(f"   {user_count} user(s) now have a user_uuid.")

            print("   Dropping bookings_readable (depends on bookings.user_id) - recreated in step 4.")
            cur.execute("DROP VIEW IF EXISTS bookings_readable")

            for table in DEPENDENT_TABLES:
                print(f"2. Migrating {table}.user_id (username -> UUID)...")
                cur.execute(f"SELECT count(*) AS n FROM {table}")
                before_count = cur.fetchone()["n"]

                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS user_uuid UUID")
                cur.execute(
                    f"UPDATE {table} t SET user_uuid = u.user_uuid "
                    f"FROM users u WHERE t.user_id = u.username AND t.user_uuid IS NULL"
                )

                # Verify: every row that HAD a non-null user_id must now have a
                # non-null user_uuid (i.e. nothing got silently orphaned by a
                # username that no longer matches any real user).
                cur.execute(
                    f"SELECT count(*) AS n FROM {table} WHERE user_id IS NOT NULL AND user_uuid IS NULL"
                )
                unmatched = cur.fetchone()["n"]
                if unmatched:
                    raise RuntimeError(
                        f"{table}: {unmatched} row(s) have a user_id with no matching user_uuid - aborting."
                    )

                cur.execute(f"ALTER TABLE {table} DROP COLUMN user_id")  # also drops its old FK
                cur.execute(f"ALTER TABLE {table} RENAME COLUMN user_uuid TO user_id")
                cur.execute(
                    f"ALTER TABLE {table} ADD CONSTRAINT {table}_user_id_fkey "
                    f"FOREIGN KEY (user_id) REFERENCES users(user_uuid) ON DELETE SET NULL"
                )

                cur.execute("SELECT count(*) AS n FROM %s" % table)  # noqa: S608
                after_count = cur.fetchone()["n"]
                if after_count != before_count:
                    raise RuntimeError(f"{table}: row count changed ({before_count} -> {after_count}) - aborting.")
                print(f"   {table}: {after_count} rows preserved, user_id is now UUID.")

            print("3. Migrating user_facts.user_id (primary key + CASCADE)...")
            cur.execute("SELECT count(*) AS n FROM user_facts")
            before_count = cur.fetchone()["n"]

            cur.execute("ALTER TABLE user_facts ADD COLUMN IF NOT EXISTS user_uuid UUID")
            cur.execute(
                "UPDATE user_facts f SET user_uuid = u.user_uuid "
                "FROM users u WHERE f.user_id = u.username AND f.user_uuid IS NULL"
            )
            cur.execute("SELECT count(*) AS n FROM user_facts WHERE user_uuid IS NULL")
            unmatched = cur.fetchone()["n"]
            if unmatched:
                raise RuntimeError(f"user_facts: {unmatched} row(s) have no matching user_uuid - aborting.")

            cur.execute("ALTER TABLE user_facts DROP COLUMN user_id")  # drops old PK + FK together
            cur.execute("ALTER TABLE user_facts RENAME COLUMN user_uuid TO user_id")
            cur.execute("ALTER TABLE user_facts ALTER COLUMN user_id SET NOT NULL")
            cur.execute("ALTER TABLE user_facts ADD PRIMARY KEY (user_id)")
            cur.execute(
                "ALTER TABLE user_facts ADD CONSTRAINT user_facts_user_id_fkey "
                "FOREIGN KEY (user_id) REFERENCES users(user_uuid) ON DELETE CASCADE"
            )

            cur.execute("SELECT count(*) AS n FROM user_facts")
            after_count = cur.fetchone()["n"]
            if after_count != before_count:
                raise RuntimeError(f"user_facts: row count changed ({before_count} -> {after_count}) - aborting.")
            print(f"   user_facts: {after_count} rows preserved, user_id is now UUID (still the primary key).")

            print("4. Re-pointing bookings_readable at the new UUID column, joined back to username for display...")
            cur.execute("""
                CREATE OR REPLACE VIEW bookings_readable AS
                SELECT
                    b.id,
                    b.session_id,
                    u.username AS user_id,
                    b.booking_type,
                    COALESCE(f.destination, h.city) AS city,
                    CASE WHEN b.booking_type = 'flight' THEN f.flight_no ELSE h.name END AS detail,
                    b.status,
                    b.contact_info,
                    b.created_at
                FROM bookings b
                LEFT JOIN users u ON u.user_uuid = b.user_id
                LEFT JOIN flights f ON b.booking_type = 'flight' AND f.id = b.reference_id
                LEFT JOIN hotels h ON b.booking_type = 'hotel' AND h.id = b.reference_id
                ORDER BY b.id
            """)

        conn.commit()
        print("\nMigration committed successfully.")
    except Exception:
        conn.rollback()
        print("\nMigration FAILED and was rolled back - database is unchanged.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

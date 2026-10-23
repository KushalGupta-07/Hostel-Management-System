import os
import pymysql
import pymysql.cursors
from config import Config

def get_db_connection():
    """Establish and return a connection to the MySQL database."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def query_db(query, args=(), one=False):
    """Execute a read query and return dictionary results."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            result = cursor.fetchone() if one else cursor.fetchall()
            return result
    finally:
        conn.close()

def execute_db(query, args=(), return_id=False):
    """Execute an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            conn.commit()
            if return_id:
                return cursor.lastrowid
            return cursor.rowcount
    finally:
        conn.close()

def sync_room_occupancy():
    """Ensure room occupancy and status match active student allocations."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Reset all room occupancies to 0
            cursor.execute("UPDATE rooms SET current_occupancy = 0 WHERE status != 'Maintenance'")
            
            # Recalculate occupancy from active students
            cursor.execute("""
                UPDATE rooms r
                JOIN (
                    SELECT room_id, COUNT(*) as active_count
                    FROM students
                    WHERE status = 'Active' AND room_id IS NOT NULL
                    GROUP BY room_id
                ) s ON r.id = s.room_id
                SET r.current_occupancy = s.active_count
            """)
            
            # Update status to 'Full' where occupancy >= capacity and status != 'Maintenance'
            cursor.execute("""
                UPDATE rooms 
                SET status = 'Full' 
                WHERE current_occupancy >= capacity AND status != 'Maintenance'
            """)
            
            # Update status to 'Available' where occupancy < capacity and status != 'Maintenance'
            cursor.execute("""
                UPDATE rooms 
                SET status = 'Available' 
                WHERE current_occupancy < capacity AND status != 'Maintenance'
            """)
            conn.commit()
    finally:
        conn.close()

def init_db():
    """Initialize database tables and seed data from schema.sql."""
    # First ensure database exists
    conn_raw = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset='utf8mb4',
        autocommit=True
    )
    try:
        with conn_raw.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME};")
    finally:
        conn_raw.close()

    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"schema.sql not found at {schema_file}")

    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split commands by semicolon, ignoring empty statements and comments
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for statement in statements:
                # Remove single-line comments from the beginning if any
                lines = [l for l in statement.splitlines() if not l.strip().startswith('--')]
                clean_stmt = '\n'.join(lines).strip()
                if clean_stmt:
                    # Prevent duplicate seed insertions if table already populated
                    upper_stmt = clean_stmt.upper()
                    if upper_stmt.startswith("INSERT"):
                        tokens = clean_stmt.split()
                        upper_tokens = [t.upper() for t in tokens]
                        if "INTO" in upper_tokens:
                            idx = upper_tokens.index("INTO")
                            if idx + 1 < len(tokens):
                                tbl_name = tokens[idx + 1].strip("` (")
                                try:
                                    cursor.execute(f"SELECT COUNT(*) as c FROM `{tbl_name}`")
                                    cnt_row = cursor.fetchone()
                                    if cnt_row and cnt_row['c'] > 0:
                                        continue
                                except Exception:
                                    pass

                    try:
                        cursor.execute(clean_stmt)
                    except pymysql.Error as e:
                        # Log but continue if already exists or minor error
                        print(f"SQL execution note: {e}")
        conn.commit()
        sync_room_occupancy()
        print("Database initialized and synchronized successfully!")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()

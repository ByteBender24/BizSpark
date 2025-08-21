import sqlite3
import os

def initialize_database():
    """Initialize SQLite database with required tables."""
    db_path = "inventory.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0.0,
                category TEXT DEFAULT '',
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on product_name for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_name 
            ON inventory(product_name)
        """)
        
        conn.commit()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")

"""
CSV to SQLite Migration Script
Migrates health_master.csv to SQLite with Full-Text Search (FTS5) index
Run once: python database/migrate.py
"""

import csv
import sqlite3
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "health_master.csv"
DB_PATH = BASE_DIR / "health_data.db"

def migrate_csv_to_sqlite():
    """Migrate CSV data to SQLite with FTS5 index"""
    
    print(f"🔄 Starting migration from {CSV_PATH} to {DB_PATH}")
    
    # Check if CSV exists
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")
    
    # Remove existing database if present
    if DB_PATH.exists():
        print(f"⚠️  Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create foods table
    print("📋 Creating foods table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fdc_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            protein REAL,
            calories REAL,
            sugar REAL,
            sodium REAL,
            portion_description TEXT,
            gram_weight REAL,
            UNIQUE(fdc_id, portion_description)
        )
    """)
    
    # Create FTS5 virtual table for fast text search
    print("🔍 Creating Full-Text Search index...")
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS foods_fts USING fts5(
            description,
            content=foods,
            content_rowid=id
        )
    """)
    
    # Create triggers to keep FTS in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS foods_ai AFTER INSERT ON foods BEGIN
            INSERT INTO foods_fts(rowid, description) VALUES (new.id, new.description);
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS foods_ad AFTER DELETE ON foods BEGIN
            DELETE FROM foods_fts WHERE rowid = old.id;
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS foods_au AFTER UPDATE ON foods BEGIN
            UPDATE foods_fts SET description = new.description WHERE rowid = new.id;
        END
    """)
    
    # Read and insert CSV data
    print("📥 Reading CSV and inserting data...")
    row_count = 0
    batch_size = 1000
    batch = []
    
    with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            batch.append((
                int(row['fdc_id']),
                row['description'],
                float(row['protein']) if row['protein'] else None,
                float(row['calories']) if row['calories'] else None,
                float(row['sugar']) if row['sugar'] else None,
                float(row['sodium']) if row['sodium'] else None,
                row['portion_description'],
                float(row['gram_weight']) if row['gram_weight'] else None
            ))
            
            if len(batch) >= batch_size:
                cursor.executemany("""
                    INSERT OR IGNORE INTO foods 
                    (fdc_id, description, protein, calories, sugar, sodium, portion_description, gram_weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                row_count += len(batch)
                batch = []
                print(f"  Inserted {row_count} rows...")
        
        # Insert remaining rows
        if batch:
            cursor.executemany("""
                INSERT OR IGNORE INTO foods 
                (fdc_id, description, protein, calories, sugar, sodium, portion_description, gram_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            row_count += len(batch)
    
    conn.commit()
    
    # Create indexes for performance
    print("⚡ Creating performance indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fdc_id ON foods(fdc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_description ON foods(description)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calories ON foods(calories)")
    
    conn.commit()
    
    # Verify migration
    cursor.execute("SELECT COUNT(*) FROM foods")
    total_rows = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT fdc_id) FROM foods")
    unique_foods = cursor.fetchone()[0]
    
    # Get database size
    db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    
    print(f"\n✅ Migration complete!")
    print(f"   Total rows: {total_rows}")
    print(f"   Unique foods: {unique_foods}")
    print(f"   Database size: {db_size_mb:.2f} MB")
    print(f"   Location: {DB_PATH}")
    
    # Test FTS search
    print(f"\n🧪 Testing FTS search for 'milk'...")
    cursor.execute("""
        SELECT f.description, f.calories, f.sugar, f.portion_description
        FROM foods_fts
        JOIN foods f ON foods_fts.rowid = f.id
        WHERE foods_fts.description MATCH 'milk'
        LIMIT 5
    """)
    results = cursor.fetchall()
    print(f"   Found {len(results)} results:")
    for desc, cal, sugar, portion in results:
        print(f"   - {desc} ({portion}): {cal} kcal, {sugar}g sugar")
    
    conn.close()
    print(f"\n🎉 Ready to use! Start the API with: uvicorn app.main:app --reload")

if __name__ == "__main__":
    migrate_csv_to_sqlite()

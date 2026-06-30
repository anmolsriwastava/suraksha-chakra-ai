import sqlite3
import random

DB_PATH = r"c:\Users\Anmol Sriwastava\OneDrive\Desktop\clone-suraksha-chakra-ai\suraksha-chakra-ai\suraksha.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE wage_reports ADD COLUMN assigned_officer VARCHAR;")
        print("Added assigned_officer column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column assigned_officer already exists.")
        else:
            raise e
            
    # 2. Populate some officers for demo data (e.g. 30% of complaints assigned to random officers)
    cursor.execute("SELECT id FROM wage_reports")
    rows = cursor.fetchall()
    
    officers = ["Insp. R. Sharma", "Insp. S. Verma", "Off. K. Singh", "Off. M. Patel"]
    
    count = 0
    for row in rows:
        if random.random() < 0.3:
            officer = random.choice(officers)
            cursor.execute("UPDATE wage_reports SET assigned_officer = ? WHERE id = ?", (officer, row[0]))
            count += 1
            
    conn.commit()
    conn.close()
    
    print(f"Migrated successfully. Assigned officers to {count} reports for the demo.")

if __name__ == "__main__":
    migrate()

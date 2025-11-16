"""
Migration script to add new columns to existing eval_results table
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env file")
    exit(1)

try:
    # Connect to database
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    
    print("🔄 Checking if columns need to be added...")
    
    # Check if columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'eval_results' 
        AND column_name IN ('user_input', 'agent_output', 'justification', 'improvements')
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    columns_to_add = {
        'user_input': 'User input/query',
        'agent_output': 'Agent output/response', 
        'justification': 'Gemini justification',
        'improvements': 'Gemini improvement suggestions'
    }
    
    missing_columns = [col for col in columns_to_add.keys() if col not in existing_columns]
    
    if not missing_columns:
        print("✅ All columns already exist! No migration needed.")
    else:
        print(f"📝 Adding {len(missing_columns)} new column(s)...")
        
        for col_name in missing_columns:
            cursor.execute(f"""
                ALTER TABLE eval_results 
                ADD COLUMN {col_name} TEXT
            """)
            print(f"  ✅ Added {col_name} column ({columns_to_add[col_name]})")
        
        connection.commit()
        print("✅ Migration completed successfully!")
    
    cursor.close()
    connection.close()
    
    print("\n🎉 Database is up to date!")
    print("You can now restart your eval server.")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    print("\nIf table doesn't exist, just restart the eval server and it will create it.")
    exit(1)

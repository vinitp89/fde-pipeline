import pandas as pd
from sqlalchemy import create_engine, text

# 1. Load the clean dataset
df = pd.read_csv("cleaned_payments.csv")

# 2. Configure the connection string
# Format: postgresql://username:password@host:port/database_name
# Replace 'your_password' with the password you set during installation
db_url = "postgresql+psycopg2://postgres:India%40123@localhost:5432/fde_audit"

# 3. Create the database engine
engine = create_engine(db_url)

# 4. Insert data directly into a new table named 'stripe_failures'
try:
    # 1. Write everything to a temporary staging table
    df.to_sql("stripe_failures_staging", engine, if_exists="replace", index=False)
    print("Data loaded to staging table.")
    
    # 2. Define the Upsert logic
    upsert_query = text("""
        INSERT INTO stripe_failures (id, amount, currency, failure_message, ingestion_date)
        SELECT id, amount, currency, failure_message, ingestion_date FROM stripe_failures_staging
        ON CONFLICT (id) DO UPDATE SET 
            amount = EXCLUDED.amount,
            failure_message = EXCLUDED.failure_message,
            ingestion_date = EXCLUDED.ingestion_date;
    """)
    
    # 3. Execute the transaction
    with engine.begin() as conn:
        conn.execute(upsert_query)
        
    print("Upsert complete. New records inserted, existing records updated.")
    
except Exception as e:
    print(f"Database error: {e}")
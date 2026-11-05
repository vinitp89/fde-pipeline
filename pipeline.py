import requests
import time
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import os

# ==========================================
# 1. EXTRACT
# ==========================================
def extract_stripe_data(secret_key):
    print("Starting Extract: Fetching from Stripe...")
    url = "https://api.stripe.com/v1/charges"
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    has_more = True
    starting_after = None
    failed_charges = []
    
    while has_more:
        params = {"limit": 100}
        if starting_after:
            params["starting_after"] = starting_after
            
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status() 
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:
                print("Rate limit hit. Sleeping for 2 seconds...")
                time.sleep(2)
                continue 
            else:
                raise Exception(f"Fatal API Error: {err}")
                
        data = response.json()
        charges = data.get("data", [])
        
        for charge in charges:
            if charge.get("status") == "failed":
                failed_charges.append({
                    "id": charge.get("id"),
                    "amount": charge.get("amount") / 100.0, 
                    "currency": charge.get("currency").upper(),
                    "failure_message": charge.get("failure_message")
                })
        
        has_more = data.get("has_more", False)
        if has_more and charges:
            starting_after = charges[-1]["id"]

    print(f"Extract Complete: {len(failed_charges)} records found.")
    # Return raw data as a DataFrame directly instead of saving to CSV
    return pd.DataFrame(failed_charges) if failed_charges else pd.DataFrame()

# ==========================================
# 2. TRANSFORM
# ==========================================
def transform_data(df):
    if df.empty:
        return df
        
    print("Starting Transform: Cleaning data...")
    df['failure_message'] = df['failure_message'].fillna('unknown_error')
    df['failure_message'] = df['failure_message'].str.lower()
    df['ingestion_date'] = datetime.now().strftime('%Y-%m-%d')
    
    print("Transform Complete.")
    return df

# ==========================================
# 3. LOAD
# ==========================================
def load_to_postgres(df, db_url):
    if df.empty:
        print("No data to load. Skipping.")
        return
        
    print("Starting Load: Pushing to PostgreSQL...")
    engine = create_engine(db_url)

    try:
        # Write to staging
        df.to_sql("stripe_failures_staging", engine, if_exists="replace", index=False)
        
        # Upsert logic
        upsert_query = text("""
            INSERT INTO stripe_failures (id, amount, currency, failure_message, ingestion_date)
            SELECT id, amount, currency, failure_message, ingestion_date FROM stripe_failures_staging
            ON CONFLICT (id) DO UPDATE SET 
                amount = EXCLUDED.amount,
                failure_message = EXCLUDED.failure_message,
                ingestion_date = EXCLUDED.ingestion_date;
        """)
        
        with engine.begin() as conn:
            conn.execute(upsert_query)
            
        print("Load Complete: Upsert successful.")
    except Exception as e:
        raise Exception(f"Database error during load: {e}")

# ==========================================
# MAIN EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    # Configuration (In a real app, these would be environment variables)
    STRIPE_KEY = os.environ.get("STRIPE_KEY")
    DB_URL = "postgresql+psycopg2://postgres:India%40123@host.docker.internal:5432/fde_audit"
    
    try:
        # Execute the ETL pipeline
        raw_df = extract_stripe_data(STRIPE_KEY)
        clean_df = transform_data(raw_df)
        load_to_postgres(clean_df, DB_URL)
        
        print("\nPipeline executed successfully! [Version 2.0 - CI/CD Active]")
        
    except Exception as e:
        print(f"\nPipeline Failed: {e}")
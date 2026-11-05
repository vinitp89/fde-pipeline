import pandas  as pd
from datetime import datetime

# Load the CSV
df = pd.read_csv("failed_payments.csv")
print("Original Data:")
print(df.head())

# Fill empty messages and lowercase everything
df['failure_message'] = df['failure_message'].fillna('unknown_error')
df['failure_message'] = df['failure_message'].str.lower()

# Add a timestamp for when this data was processed
df['ingestion_date'] = datetime.now().strftime('%Y-%m-%d')

print("\nCleaned Data:")
print(df.head())

# Save the clean version
df.to_csv("cleaned_payments.csv", index=False)
print("\nSaved to cleaned_payments.csv")
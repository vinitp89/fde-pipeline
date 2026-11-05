import requests
import time
import pandas as pd
import os

STRIPE_SECRET_KEY = os.environ.get("STRIPE_KEY")
url = "https://api.stripe.com/v1/charges"

headers = {
    "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
    "Content-Type": "application/x-www-form-urlencoded"
}

has_more = True
starting_after = None
failed_charges = []

while has_more:
    try:
        params = {
            "limit": 100
        }
        if starting_after:
            params["starting_after"] = starting_after

        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        charges = data.get("data", [])

        for charge in charges:
            if charge.get("status") == "failed":
                failed_charges.append({
                    "id": charge.get("id"),
                    "amount": charge.get("amount"),
                    "currency": charge.get("currency").upper(),
                    "failure_message": charge.get("failure_message")
            })
        
        has_more = data.get("has_more", False)
        if has_more and charges:
            starting_after = charges[-1]["id"] # Get ID of the last item

        print(f"\nAudit Complete! Found {len(failed_charges)} failed transactions.")
        
        if failed_charges:
            df = pd.DataFrame(failed_charges)
            print("\nStructured Data:")
            print(df.head()) 
            df.to_csv("failed_payments.csv", index=False)
            print("\nData exported to failed_payments.csv")
        else:
            print("No failed transactions to process.")

    except requests.exceptions.HTTPError as err:
        if response.status_code == 429:
            print("Rate limit hit. Sleeping for 2 seconds...")
            time.sleep(2)
            continue # Retry the exact same request
        else:
            print(f"API Error: {err}")
            break
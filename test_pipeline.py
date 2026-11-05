import pandas as pd
from pipeline import transform_data

def test_transform_data_cleans_messages():
    # 1. ARRANGE: Create fake, raw data that mimics what Stripe would return
    raw_data = [
        {
            "id": "ch_123",
            "amount": 50.0,
            "currency": "USD",
            "failure_message": "INSUFFICIENT_FUNDS" 
        }, 
        {
            "id": "ch_124",
            "amount": 25.0,
            "currency": "USD",
            "failure_message": None 
        }
    ]
    raw_df = pd.DataFrame(raw_data)

    # 2. ACT: Pass the fake data through your function
    clean_df = transform_data(raw_df)

    # 3. ASSERT: Verify the function transformed the data correctly
    assert clean_df.iloc[0]['failure_message'] == "insufficient_funds"
    assert clean_df.iloc[1]['failure_message'] == "unknown_error"
    assert 'ingestion_date' in clean_df.columns
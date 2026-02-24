import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from google.cloud import storage

# Config
load_dotenv()
TSM_API_KEY = os.getenv("TSM_API_KEY")
AH_ID = os.getenv("AH_ID")
GCP_PROJECT = os.getenv("GCP_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def get_access_token():
    print(f"Using key: {repr(TSM_API_KEY)}")
    response = requests.post(
        "https://auth.tradeskillmaster.com/oauth2/token",
        json={
            "client_id": "c260f00d-1071-409a-992f-dda2e5498536",
            "grant_type": "api_token",
            "scope": "app:realm-api app:pricing-api",
            "token": TSM_API_KEY,
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]

def fetch_ah_data(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"https://pricing-api.tradeskillmaster.com/ah/{AH_ID}",
        headers=headers
    )

    response.raise_for_status()
    return response.json()

def upload_to_gcs(data, timestamp):
    client = storage.Client(project=GCP_PROJECT)
    bucket = client.bucket(BUCKET_NAME)

    filename = f"ah_snapshots/{timestamp}.ndjson"
    blob = bucket.blob(filename)

    lines = []
    for item in data:
        record = {
            "snapshot_time": timestamp,
            **item
        }
        lines.append(json.dumps(record))
    
    ndjson_content = "\n".join(lines)

    blob.upload_from_string(
        ndjson_content,
        content_type="application/x-ndjson"
    )
    print(f"Uploaded {len(data)} items to gs://{BUCKET_NAME}/{filename}")

def run():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{timestamp}] Starting fetch...")

    print("Getting access token...")
    token = get_access_token()

    print("Fetching AH data...")
    data = fetch_ah_data(token)
    print(f"Got {len(data)} items")

    print("Uploading to GCS...")
    upload_to_gcs(data, timestamp)

    print("Done!")


if __name__ == "__main__":
    run()
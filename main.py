from fastapi import FastAPI
from google.cloud import bigquery
from dotenv import load_dotenv
import os

load_dotenv()
GCP_PROJECT = os.getenv("GCP_PROJECT")

app = FastAPI()

client = bigquery.Client(GCP_PROJECT)

@app.get("/item/{item_name}")
def get_item_price(item_name: str):
    query = """
        SELECT item.ID, item.Display_lang, rd.minBuyout, rd.quantity, rd.numAuctions, rd.marketValue, rd.snapshot_time
        FROM `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.item_names` as item
        LEFT JOIN `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.raw_data` as rd
        ON item.ID = rd.itemId
        WHERE LOWER(item.Display_lang) LIKE LOWER(@item_name)
        LIMIT 20
        """

    job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("item_name", "STRING", f"%{item_name}%") # prevent SQL injection by ensuring any searches are literal strings
    ]
)

    results = client.query(query, job_config=job_config).result()
    return [dict(row) for row in results]
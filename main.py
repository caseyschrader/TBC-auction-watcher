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
    # Display_lang = item name
    query = """
        SELECT item.ID, item.Display_lang, rd.minBuyout, rd.quantity, rd.numAuctions, rd.marketValue, rd.snapshot_time
        FROM `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.item_names` as item
        INNER JOIN `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.raw_data` as rd
        ON item.ID = rd.itemId
        WHERE LOWER(item.Display_lang) LIKE (@item_name)
            AND rd.numAuctions > 0
            AND rd.snapshot_time = (SELECT MAX(snapshot_time) FROM `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.raw_data`)
        ORDER BY rd.numAuctions DESC
        LIMIT 50
        """

    job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("item_name", "STRING", f"%{item_name.lower()}%") # prevent SQL injection by ensuring any searches are literal strings
    ]
)

    results = client.query(query, job_config=job_config).result()
    return [dict(row) for row in results]

@app.get("/item/{item_id}/history")
def get_item_price_history(item_id: int, days: int = 7):
    query = """
        SELECT
            rd.snapshot_time,
            rd.minBuyout,
            rd.marketValue,
            rd.numAuctions,
            rd.quantity,
            -- 24-snapshot mean and stddev
            AVG(rd.marketValue) OVER (
                ORDER BY rd.snapshot_time
                ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
            ) AS mean,
            STDDEV(rd.marketValue) OVER (
                ORDER BY rd.snapshot_time
                ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
            ) AS stddev
        FROM `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.raw_data` AS rd
        WHERE rd.itemId = @item_id
          AND rd.snapshot_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
        ORDER BY rd.snapshot_time ASC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("item_id", "INT64", item_id),
            bigquery.ScalarQueryParameter("days", "INT64", days),
        ]
    )

@app.get("/item/{item_id}/dow")
def get_day_of_week_analysis(item_id: int):
    query = """
        SELECT
            EXTRACT(DAYOFWEEK FROM snapshot_time) AS day_num,
            CASE EXTRACT(DAYOFWEEK FROM snapshot_time)
                WHEN 1 THEN 'Sunday'
                WHEN 2 THEN 'Monday'
                WHEN 3 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END AS day_of_week,
            AVG(marketValue) AS avg_market_value,
            AVG(minBuyout) AS avg_min_buyout,
            COUNT(*) AS snapshot_count
        FROM `project-f929cf6e-3eec-4c5c-85a.tsm_ah_data.raw_data`
        WHERE itemId = @item_id
        GROUP BY day_of_week
        ORDER BY day_num

    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("item_id", "INT64", item_id),
        ]
    )

    results = client.query(query, job_config=job_config).result()
    return [dict(row) for row in results]
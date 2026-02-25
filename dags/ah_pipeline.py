import os
from dotenv import load_dotenv
from airflow.decorators import dag
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from fetcher import run as fetch_tsm_data

load_dotenv()
AH_ID = os.getenv("AH_ID")
GCP_PROJECT = os.getenv("GCP_PROJECT")
BUCKET_NAME = os.getenv("BUCKET_NAME")


default_args = {
    'start_date': datetime(2026, 2, 25),
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_retry': False
}

@dag(
    default_args=default_args,
    description='Fetches data from TSM auction house API and loads it into Cloud Storage',
    schedule_interval='@hourly',
    start_date=datetime(2026,2,25),
    catchup=False
)

def ah_pipeline():
    fetch_task = PythonOperator(
        task_id='fetch_tsm_data',
        python_callable=fetch_tsm_data
    )

    load_task = GCSToBigQueryOperator(
        task_id='load_to_bigquery',
        bucket=BUCKET_NAME,
        source_objects=["{{ ti.xcom_pull(task_ids='fetch_tsm_data') }}"],
        destination_project_dataset_table=f'{GCP_PROJECT}.tsm_ah_data.raw_data',
        source_format='NEWLINE_DELIMITED_JSON',
        write_disposition='WRITE_APPEND',
        autodetect=True,
        gcp_conn_id='google_cloud_default',
    )

    fetch_task >> load_task

ah_pipeline()



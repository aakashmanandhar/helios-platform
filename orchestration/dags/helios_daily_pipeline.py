from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

HELIOS_ROOT = "/opt/helios"

default_args = {
    "owner": "helios-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="helios_daily_pipeline",
    description="Extract all Helios batch sources into bronze, then run dbt through silver/gold and analytics marts.",
    default_args=default_args,
    schedule=None,  # in production: "0 6 * * *" for a daily 6am run
    start_date=datetime(2026, 7, 1),
    catchup=False,
    tags=["helios", "medallion", "batch"],
    max_active_runs=1,
) as dag:

    extract_orders = BashOperator(
        task_id="extract_postgres_oltp_to_bronze",
        bash_command=f"python3 {HELIOS_ROOT}/ingestion/export_postgres_to_bronze.py",
    )

    extract_marketing = BashOperator(
        task_id="extract_marketing_feeds",
        bash_command=f"python3 {HELIOS_ROOT}/ingestion/ingest_marketing_feeds.py",
    )

    extract_payments = BashOperator(
        task_id="extract_payments_feed",
        bash_command=f"python3 {HELIOS_ROOT}/ingestion/ingest_payments_feed.py",
    )

    extract_support = BashOperator(
        task_id="extract_support_feed",
        bash_command=f"python3 {HELIOS_ROOT}/ingestion/ingest_support_feed.py",
    )

    extract_shipping = BashOperator(
        task_id="extract_shipping_feed",
        bash_command=f"python3 {HELIOS_ROOT}/ingestion/ingest_shipping_feed.py",
    )

    extract_weather = BashOperator(
        task_id="extract_weather_feed",
        bash_command=f"python3 {HELIOS_ROOT}/ingestion/ingest_weather_feed.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {HELIOS_ROOT}/warehouse && DBT_PROFILES_DIR={HELIOS_ROOT}/warehouse dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {HELIOS_ROOT}/warehouse && DBT_PROFILES_DIR={HELIOS_ROOT}/warehouse dbt test",
    )

    [extract_orders, extract_marketing, extract_payments, extract_support, extract_shipping, extract_weather] >> dbt_run >> dbt_test

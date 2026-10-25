import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from dotenv import load_dotenv

sys.path.insert(0, "/opt/airflow/src")

from extract_data import extract_weather_data
from load_data import load_weather_data
from quality_checks import validate_weather_data
from transform_data import data_transformations

env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("API_KEY")
PARQUET_PATH = "/opt/airflow/data/temp_data.parquet"
TABLE_NAME = "weather_data"


@dag(
    dag_id="youtube_weather_pipeline",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    description="Pipeline ETL - Clima de 10 Capitais Brasileiras (com Data Quality e UPSERT)",
    schedule="0 */1 * * *",
    start_date=datetime(2026, 2, 7),
    catchup=False,
    tags=["weather", "etl", "brazil", "portfolio"],
)
def weather_pipeline():
    @task
    def extract():
        extract_weather_data(API_KEY)

    @task
    def transform():
        df = data_transformations()
        df.to_parquet(PARQUET_PATH, index=False)

    @task
    def quality_check():
        import pandas as pd

        df = pd.read_parquet(PARQUET_PATH)
        validate_weather_data(df)

    @task
    def load():
        import pandas as pd

        df = pd.read_parquet(PARQUET_PATH)
        load_weather_data(TABLE_NAME, df)

    extract() >> transform() >> quality_check() >> load()


weather_pipeline()

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.extract_data import extract_weather_data
from src.load_data import load_weather_data
from src.quality_checks import validate_weather_data
from src.transform_data import data_transformations

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

env_path = Path(__file__).resolve().parent / "config" / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("API_KEY")
TABLE_NAME = "weather_data"


def pipeline():
    logging.info("ETAPA 1: EXTRACT (10 Capitais Brasileiras)")
    records = extract_weather_data(API_KEY)
    if not records:
        return

    logging.info("ETAPA 2: TRANSFORM")
    df = data_transformations()

    logging.info("ETAPA 3: DATA QUALITY CHECK")
    validate_weather_data(df)

    logging.info("ETAPA 4: LOAD (UPSERT no PostgreSQL)")
    load_weather_data(TABLE_NAME, df)

    print("\n" + "=" * 70)
    print("✅ Pipeline ETL Multi-Capitais executado com sucesso (sem duplicatas)!")
    print("=" * 70)


if __name__ == "__main__":
    pipeline()

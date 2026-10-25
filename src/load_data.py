import logging
import os
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
load_dotenv(env_path)

user = os.getenv("user", "airflow")
password = os.getenv("password", "airflow")
database = os.getenv("database", "airflow")

in_docker = Path("/.dockerenv").exists()
host = "postgres" if in_docker else os.getenv("host", "localhost")
port = "5432" if in_docker else os.getenv("port", "5433")


def get_engine():
    logging.info(f"Conectando ao PostgreSQL em {host}:{port}/{database}...")
    return create_engine(
        f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{database}"
    )


def get_weather_table(metadata: MetaData, table_name: str) -> Table:
    return Table(
        table_name,
        metadata,
        Column("datetime", DateTime(timezone=True), primary_key=True),
        Column("city_id", BigInteger, primary_key=True),
        Column("city_name", String(100), nullable=False),
        Column("state", String(10)),
        Column("region", String(30)),
        Column("country", String(10)),
        Column("latitude", Float),
        Column("longitude", Float),
        Column("weather_id", Integer),
        Column("weather_main", String(50)),
        Column("weather_description", String(120)),
        Column("temperature", Float),
        Column("feels_like", Float),
        Column("temp_min", Float),
        Column("temp_max", Float),
        Column("pressure", Integer),
        Column("humidity", Integer),
        Column("sea_level", Integer),
        Column("grnd_level", Integer),
        Column("visibility", Integer),
        Column("wind_speed", Float),
        Column("wind_deg", Integer),
        Column("wind_gust", Float),
        Column("rain_1h", Float),
        Column("clouds", Integer),
        Column("sunrise", DateTime(timezone=True)),
        Column("sunset", DateTime(timezone=True)),
        Column("timezone", Integer),
        Column("ingested_at", DateTime(timezone=True)),
    )


def load_weather_data(table_name: str, df: pd.DataFrame) -> None:
    engine = get_engine()
    metadata = MetaData()
    weather_table = get_weather_table(metadata, table_name)
    metadata.create_all(engine)

    records = [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df.to_dict(orient="records")
    ]

    stmt = pg_insert(weather_table).values(records)
    update_cols = {
        col.name: stmt.excluded[col.name]
        for col in weather_table.columns
        if not col.primary_key
    }
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["city_id", "datetime"],
        set_=update_cols,
    )

    with engine.begin() as conn:
        conn.execute(upsert_stmt)
        total = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

    logging.info(
        f"UPSERT concluído em '{table_name}' ({len(records)} registros processados sem duplicatas)!"
    )
    logging.info(f"Total acumulado na tabela '{table_name}': {total}")

    logging.info(
        f"UPSERT concluído em '{table_name}' ({len(records)} registros processados sem duplicatas)!"
    )
    logging.info(f"Total acumulado na tabela '{table_name}': {total}")


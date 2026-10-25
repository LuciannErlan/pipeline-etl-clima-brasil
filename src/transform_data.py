import json
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

path_name = Path(__file__).resolve().parent.parent / "data" / "weather_data.json"

columns_names_to_drop = ["weather", "weather_icon", "sys.type"]

columns_names_to_rename = {
    "base": "base",
    "visibility": "visibility",
    "dt": "datetime",
    "timezone": "timezone",
    "id": "city_id",
    "name": "city_name",
    "state": "state",
    "region": "region",
    "cod": "code",
    "coord.lon": "longitude",
    "coord.lat": "latitude",
    "main.temp": "temperature",
    "main.feels_like": "feels_like",
    "main.temp_min": "temp_min",
    "main.temp_max": "temp_max",
    "main.pressure": "pressure",
    "main.humidity": "humidity",
    "main.sea_level": "sea_level",
    "main.grnd_level": "grnd_level",
    "wind.speed": "wind_speed",
    "wind.deg": "wind_deg",
    "wind.gust": "wind_gust",
    "rain.1h": "rain_1h",
    "clouds.all": "clouds",
    "sys.id": "sys_id",
    "sys.country": "country",
    "sys.sunrise": "sunrise",
    "sys.sunset": "sunset",
}

columns_to_normalize_datetime = ["datetime", "sunrise", "sunset"]

final_columns = [
    "datetime",
    "city_id",
    "city_name",
    "state",
    "region",
    "country",
    "latitude",
    "longitude",
    "weather_id",
    "weather_main",
    "weather_description",
    "temperature",
    "feels_like",
    "temp_min",
    "temp_max",
    "pressure",
    "humidity",
    "sea_level",
    "grnd_level",
    "visibility",
    "wind_speed",
    "wind_deg",
    "wind_gust",
    "rain_1h",
    "clouds",
    "sunrise",
    "sunset",
    "timezone",
    "ingested_at",
]


def create_dataframe(path: Path) -> pd.DataFrame:
    logging.info("Criando DataFrame a partir do arquivo JSON...")
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    df = pd.json_normalize(data)
    logging.info(
        f"DataFrame bruto criado com {len(df)} linha(s) e {len(df.columns)} colunas."
    )
    return df


def normalize_weather_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_weather = pd.json_normalize(df["weather"].apply(lambda x: x[0]))
    df_weather = df_weather.rename(
        columns={
            "id": "weather_id",
            "main": "weather_main",
            "description": "weather_description",
            "icon": "weather_icon",
        }
    )
    df = pd.concat([df.reset_index(drop=True), df_weather.reset_index(drop=True)], axis=1)
    logging.info(f"Coluna 'weather' desaninhada ({len(df.columns)} colunas).")
    return df


def drop_columns(df: pd.DataFrame, columns_names: list[str]) -> pd.DataFrame:
    df = df.drop(columns=columns_names, errors="ignore")
    return df


def rename_and_standardize_columns(
    df: pd.DataFrame, columns_names: dict[str, str]
) -> pd.DataFrame:
    df = df.rename(columns=columns_names)
    df["ingested_at"] = pd.Timestamp.now(tz="America/Sao_Paulo")

    for col in final_columns:
        if col not in df.columns:
            df[col] = 0.0 if col in ("rain_1h", "wind_gust") else None

    df["rain_1h"] = df["rain_1h"].fillna(0.0)
    df["wind_gust"] = df["wind_gust"].fillna(0.0)
    df["weather_description"] = df["weather_description"].str.capitalize()

    df = df[final_columns]
    logging.info("Colunas renomeadas, padronizadas e enriquecidas.")
    return df


def normalize_datetime_columns(
    df: pd.DataFrame, columns_names: list[str]
) -> pd.DataFrame:
    for name in columns_names:
        df[name] = pd.to_datetime(df[name], unit="s", utc=True).dt.tz_convert(
            "America/Sao_Paulo"
        )
    logging.info("Colunas de horário convertidas para fuso America/Sao_Paulo.")
    return df


def data_transformations() -> pd.DataFrame:
    logging.info("Iniciando transformações nos dados...")
    df = create_dataframe(path_name)
    df = normalize_weather_columns(df)
    df = drop_columns(df, columns_names_to_drop)
    df = rename_and_standardize_columns(df, columns_names_to_rename)
    df = normalize_datetime_columns(df, columns_to_normalize_datetime)
    df = df.drop_duplicates(subset=["city_id", "datetime"], keep="last")
    logging.info(f"Transformações concluídas: {len(df)} registros prontos!")
    return df

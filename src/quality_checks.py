import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def validate_weather_data(df: pd.DataFrame) -> None:
    """Executa verificações de Qualidade de Dados (Data Quality) antes da carga no banco."""
    logging.info("Executando verificações de Qualidade de Dados (Data Quality)...")

    if df.empty:
        raise ValueError("Data Quality falhou: o DataFrame está vazio.")

    required_cols = ["city_id", "city_name", "datetime", "temperature", "humidity"]
    for col in required_cols:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            raise ValueError(
                f"Data Quality falhou: coluna obrigatória '{col}' possui {null_count} valor(es) nulo(s)."
            )

    invalid_temp = df[(df["temperature"] < -50) | (df["temperature"] > 60)]
    if not invalid_temp.empty:
        raise ValueError(
            f"Data Quality falhou: temperatura fora da faixa realista (-50°C a 60°C): "
            f"{invalid_temp[['city_name', 'temperature']].to_dict(orient='records')}"
        )

    invalid_humidity = df[(df["humidity"] < 0) | (df["humidity"] > 100)]
    if not invalid_humidity.empty:
        raise ValueError(
            f"Data Quality falhou: umidade fora de 0%-100%: "
            f"{invalid_humidity[['city_name', 'humidity']].to_dict(orient='records')}"
        )

    duplicates = int(df.duplicated(subset=["city_id", "datetime"]).sum())
    if duplicates > 0:
        raise ValueError(
            f"Data Quality falhou: {duplicates} registro(s) duplicado(s) para (city_id, datetime)."
        )

    logging.info(
        f"Data Quality aprovado com sucesso para {len(df)} registro(s) sem anomalias!"
    )


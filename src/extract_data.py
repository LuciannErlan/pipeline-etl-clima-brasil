import json
import logging
from pathlib import Path
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

BRAZIL_CAPITALS = [
    {"query": "Sao Paulo,BR", "state": "SP", "region": "Sudeste"},
    {"query": "Rio de Janeiro,BR", "state": "RJ", "region": "Sudeste"},
    {"query": "Belo Horizonte,BR", "state": "MG", "region": "Sudeste"},
    {"query": "Curitiba,BR", "state": "PR", "region": "Sul"},
    {"query": "Porto Alegre,BR", "state": "RS", "region": "Sul"},
    {"query": "Brasilia,BR", "state": "DF", "region": "Centro-Oeste"},
    {"query": "Salvador,BR", "state": "BA", "region": "Nordeste"},
    {"query": "Recife,BR", "state": "PE", "region": "Nordeste"},
    {"query": "Fortaleza,BR", "state": "CE", "region": "Nordeste"},
    {"query": "Manaus,BR", "state": "AM", "region": "Norte"},
]

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def extract_weather_data(api_key: str, cities: list[dict] | None = None) -> list[dict]:
    if not api_key:
        raise ValueError("API_KEY não encontrada! Verifique o arquivo config/.env.")

    target_cities = cities or BRAZIL_CAPITALS
    collected_records: list[dict] = []

    logging.info(f"Iniciando extração para {len(target_cities)} capitais brasileiras...")

    for city in target_cities:
        params = {
            "q": city["query"],
            "units": "metric",
            "lang": "pt_br",
            "appid": api_key,
        }
        response = requests.get(BASE_URL, params=params, timeout=30)
        payload = response.json()

        if response.status_code != 200:
            logging.error(
                f"Erro ao buscar {city['query']} (Status {response.status_code}): "
                f"{payload.get('message', payload)}"
            )
            continue

        payload["state"] = city["state"]
        payload["region"] = city["region"]
        collected_records.append(payload)

    if not collected_records:
        logging.warning("Nenhum dado retornado pela API.")
        return []

    output_path = Path(__file__).resolve().parent.parent / "data" / "weather_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(collected_records, f, indent=4, ensure_ascii=False)

    logging.info(
        f"Extração concluída: {len(collected_records)} cidades salvas em {output_path}"
    )
    return collected_records

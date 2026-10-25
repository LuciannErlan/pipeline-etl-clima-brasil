# 🌤️ Pipeline ETL & Dashboard Climático — Capitais do Brasil

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://clima-brasil-luciann.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-3776AB?logo=python&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-3.1.7-017CEE?logo=apacheairflow&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

Projeto completo de **Engenharia de Dados de ponta a ponta**: extrai dados meteorológicos em tempo real de **10 capitais brasileiras** (nas 5 regiões do país) via API da OpenWeatherMap, aplica limpeza, padronização e validações de **Data Quality** com **Python/Pandas**, armazena de forma idempotente (**UPSERT**) no **PostgreSQL**, orquestra execuções horárias com **Apache Airflow** e disponibiliza análises interativas em um **Dashboard Streamlit + Plotly** (local e publicado na nuvem) e **Jupyter Notebook** — tudo containerizado com **Docker Compose**.

👉 **Demonstração ao vivo:** [**Monitor Climático Brasil no Streamlit Cloud**](https://clima-brasil-luciann.streamlit.app/)

> Projeto evoluído a partir da base do tutorial de [@vbluuiza](https://github.com/vbluuiza/pipeline_etl_weather_data_tutorial_youtube), expandido com coleta multi-capitais, camada de Data Quality, carga idempotente sem duplicatas e dashboard analítico em tempo real.

---

## 📸 Vitrine do Projeto

### 📊 Dashboard Analítico Interativo ([Acessar ao vivo no Streamlit Cloud](https://clima-brasil-luciann.streamlit.app/))
[![Dashboard Streamlit](assets/dashboard_streamlit.png)](https://clima-brasil-luciann.streamlit.app/)

### ⚙️ Orquestração do Pipeline no Apache Airflow (`extract >> transform >> quality_check >> load`)
![Execuções da DAG no Apache Airflow](assets/airflow_dag.png)

---

## 🏗️ Arquitetura de Dados

```mermaid
flowchart LR
    API["🌐 OpenWeatherMap API\n(10 Capitais do Brasil)"] --> E["📥 Extract\nsrc/extract_data.py"]
    E --> JSON["📄 Raw Layer\ndata/weather_data.json"]
    JSON --> T["🔄 Transform\nsrc/transform_data.py"]
    T --> PQ["📦 Staging\ntemp_data.parquet"]
    PQ --> DQ["✅ Data Quality\nsrc/quality_checks.py"]
    DQ --> L["💾 Load (UPSERT)\nsrc/load_data.py"]
    L --> DB[("🐘 PostgreSQL 16\nTabela: weather_data")]
    DB --> ST["📊 Dashboard Interativo\nStreamlit + Plotly (:8501 / Cloud)"]
    DB --> NB["📓 Análise Exploratória\nnotebooks/analysis_data.ipynb"]
```

*(Orquestrado automaticamente a cada 1 hora pelo **Apache Airflow 3.1.7** na porta `:8080`)*

---

## ✨ Diferenciais de Engenharia Implementados

- **Coleta Nacional Multi-Cidades:** Monitoramento simultâneo de 10 capitais cobrindo Norte, Nordeste, Centro-Oeste, Sudeste e Sul (São Paulo, Rio de Janeiro, Belo Horizonte, Curitiba, Porto Alegre, Brasília, Salvador, Recife, Fortaleza e Manaus).
- **Idempotência com `UPSERT` (`ON CONFLICT DO UPDATE`):** Chave primária composta `(city_id, datetime)` no PostgreSQL garantindo zero duplicidade mesmo em reexecuções manuais ou *retries* do Airflow.
- **Proteção contra *Schema Drift*:** Tratamento de campos sazonais da API (como `rain.1h` em dias de chuva ou `wind.gust`) mantendo o esquema relacional consistente.
- **Camada dedicada de *Data Quality* (`src/quality_checks.py`):** Validação automática de nulos, duplicatas em lote e limites físicos realistas de temperatura (`-50 °C` a `60 °C`) e umidade (`0%` a `100%`) antes da escrita no banco.
- **Dashboard Híbrido Containerizado e em Nuvem (`dashboard/app.py`):** Conecta automaticamente ao PostgreSQL local via Docker e opera online no [Streamlit Community Cloud](https://clima-brasil-luciann.streamlit.app/) com mapa interativo do Brasil, comparativo de Temperatura Real vs. Sensação Térmica, correlações regionais, série histórica e exportação para CSV.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologias |
|---|---|
| **Linguagem & Dados** | Python 3.12/3.13, Pandas, PyArrow (Parquet) |
| **Banco de Dados** | PostgreSQL 16, SQLAlchemy, Psycopg2 |
| **Orquestração** | Apache Airflow 3.1.7 (CeleryExecutor + Redis) |
| **Visualização & EDA** | Streamlit, Plotly, Matplotlib, Seaborn, Jupyter Notebook |
| **Infraestrutura & Deploy** | Docker, Docker Compose, Streamlit Community Cloud |

---

## 🚀 Como Executar o Projeto

> 💡 **Quer testar sem instalar nada?** Acesse diretamente a versão publicada na nuvem: **[clima-brasil-luciann.streamlit.app](https://clima-brasil-luciann.streamlit.app/)**

### 1. Pré-requisitos
- **Docker Desktop** instalado e em execução
- Chave gratuita da [OpenWeatherMap API](https://openweathermap.org/api)

### 2. Configurar Variáveis de Ambiente
Copie o arquivo `config/.env.example` para `config/.env` e adicione sua chave da API:

```env
API_KEY=sua_chave_openweathermap_aqui
user=airflow
password=airflow
database=airflow
host=localhost
port=5433
```

### 3. Subir Todos os Serviços com Docker
```powershell
docker compose up -d --build
```

### 4. Acessar as Interfaces
- **Dashboard Online (Streamlit Cloud):** https://clima-brasil-luciann.streamlit.app/
- **Apache Airflow Local (Orquestrador):** http://localhost:8080 *(login: `airflow` / `airflow`)*
- **Dashboard Climático Local (Docker):** http://localhost:8501
- **PostgreSQL (Acesso externo):** `localhost:5433` *(banco: `airflow`, tabela: `weather_data`)*

### 5. Desligar o Ambiente
```powershell
docker compose down
```

---

## 📂 Estrutura de Pastas

```text
├── assets/                   # Capturas de tela do Dashboard e do Apache Airflow
├── config/
│   └── .env.example          # Modelo de variáveis de ambiente
├── dags/
│   └── weather_dag.py        # DAG do Airflow (extract >> transform >> quality_check >> load)
├── dashboard/
│   ├── Dockerfile            # Imagem Docker do Dashboard
│   ├── requirements.txt      # Dependências para deploy no Streamlit Cloud
│   └── app.py                # Aplicação interativa em Streamlit + Plotly
├── data/                     # Camada de armazenamento local (JSON bruto e Parquet temporário)
├── notebooks/
│   └── analysis_data.ipynb   # Notebook de Análise Exploratória de Dados (EDA)
├── src/
│   ├── extract_data.py       # Extração multi-capitais via API REST
│   ├── transform_data.py     # Limpeza, normalização e fuso horário
│   ├── quality_checks.py     # Regras de validação e qualidade dos dados
│   └── load_data.py          # Modelagem da tabela e UPSERT no PostgreSQL
├── Dockerfile                # Imagem customizada do Airflow com Pandas/PyArrow
├── docker-compose.yaml       # Orquestração dos containers (Postgres, Redis, Airflow, Streamlit)
├── main.py                   # Executor local do pipeline completo
└── requirements.txt          # Dependências do ambiente virtual Python
```

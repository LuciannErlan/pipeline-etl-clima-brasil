import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.extract_data import extract_weather_data
from src.load_data import load_weather_data
from src.quality_checks import validate_weather_data
from src.transform_data import data_transformations

load_dotenv(ROOT_DIR / "config" / ".env")

st.set_page_config(
    page_title="Monitor Climático Brasil | Pipeline ETL",
    page_icon="🌤️",
    layout="wide",
)


def get_api_key() -> str | None:
    env_key = os.getenv("API_KEY")
    if env_key:
        return env_key
    try:
        return st.secrets.get("API_KEY")
    except Exception:
        return None


def get_db_engine():
    user = os.getenv("user", "airflow")
    password = os.getenv("password", "airflow")
    database = os.getenv("database", "airflow")
    in_docker = Path("/.dockerenv").exists()
    host = "postgres" if in_docker else os.getenv("host", "localhost")
    port = "5432" if in_docker else os.getenv("port", "5433")
    return create_engine(
        f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{database}",
        connect_args={"connect_timeout": 2},
    )


@st.cache_data(ttl=60)
def try_load_postgres_data() -> tuple[pd.DataFrame, bool]:
    engine = get_db_engine()
    query = """
        SELECT *
        FROM weather_data
        ORDER BY datetime DESC, city_name ASC
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, con=conn)
        if not df.empty:
            for col in ("datetime", "sunrise", "sunset", "ingested_at"):
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], utc=True).dt.tz_convert(
                        "America/Sao_Paulo"
                    )
        return df, True
    except Exception:
        return pd.DataFrame(), False


@st.cache_data(ttl=600)
def fetch_cloud_live_data(api_key: str) -> pd.DataFrame:
    records = extract_weather_data(api_key)
    if not records:
        return pd.DataFrame()
    df = data_transformations()
    validate_weather_data(df)
    return df


def run_etl_now(is_postgres_available: bool) -> tuple[bool, str]:
    try:
        api_key = get_api_key()
        if not api_key:
            return False, "API_KEY não configurada."
        records = extract_weather_data(api_key)
        if not records:
            return False, "A API não retornou registros."
        df = data_transformations()
        validate_weather_data(df)
        if is_postgres_available:
            load_weather_data("weather_data", df)
        st.cache_data.clear()
        return True, f"Coleta concluída para {len(df)} capitais!"
    except Exception as exc:
        return False, f"Erro ao executar pipeline: {exc}"


# --- Cabeçalho ---
st.title("🌤️ Monitor Climático das Capitais Brasileiras")
st.caption(
    "Dashboard analítico alimentado pelo Pipeline ETL (OpenWeatherMap API → Python/Pandas → PostgreSQL → Apache Airflow)"
)

df_all, is_postgres = try_load_postgres_data()

if not is_postgres:
    cloud_api_key = get_api_key()
    if not cloud_api_key:
        st.error(
            "Chave `API_KEY` não encontrada! No Streamlit Cloud, adicione `API_KEY = \"sua_chave\"` em **Settings → Secrets**."
        )
        st.stop()
    df_all = fetch_cloud_live_data(cloud_api_key)

# --- Barra Lateral ---
with st.sidebar:
    st.header("⚙️ Controles do Pipeline")
    if is_postgres:
        st.caption("🐘 **Fonte ativa:** PostgreSQL (Pipeline Local)")
    else:
        st.caption("☁️ **Fonte ativa:** API em Tempo Real (Streamlit Cloud)")

    if st.button("⚡ Coletar Clima Agora (ETL)", width="stretch", type="primary"):
        with st.spinner("Executando Extract → Transform → Quality → Load..."):
            ok, msg = run_etl_now(is_postgres)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if st.button("🔄 Atualizar Dados", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.divider()

if df_all.empty:
    st.warning(
        "Ainda não há dados carregados. Clique em **⚡ Coletar Clima Agora (ETL)** na barra lateral para buscar os dados!"
    )
    st.stop()

# Filtros na barra lateral
with st.sidebar:
    st.header("🔎 Filtros")
    available_regions = sorted(df_all["region"].dropna().unique().tolist())
    selected_regions = st.multiselect(
        "Regiões do Brasil",
        options=available_regions,
        default=available_regions,
    )

    filtered_cities = sorted(
        df_all[df_all["region"].isin(selected_regions)]["city_name"].unique().tolist()
    )
    selected_cities = st.multiselect(
        "Capitais",
        options=filtered_cities,
        default=filtered_cities,
    )

df_filtered = df_all[
    df_all["region"].isin(selected_regions) & df_all["city_name"].isin(selected_cities)
].copy()

if df_filtered.empty:
    st.info("Selecione ao menos uma região e uma capital nos filtros laterais.")
    st.stop()

# Snapshot mais recente de cada capital
df_latest = (
    df_filtered.sort_values("datetime", ascending=False)
    .drop_duplicates(subset=["city_id"], keep="first")
    .sort_values("temperature", ascending=False)
    .reset_index(drop=True)
)

# --- KPIs Principais ---
hottest = df_latest.iloc[0]
coldest = df_latest.iloc[-1]
rainiest = df_latest.sort_values("rain_1h", ascending=False).iloc[0]
avg_humidity = df_latest["humidity"].mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "🔥 Mais Quente Agora",
    f"{hottest['temperature']:.1f} °C",
    f"{hottest['city_name']} ({hottest['state']})",
)
col2.metric(
    "❄️ Mais Amena Agora",
    f"{coldest['temperature']:.1f} °C",
    f"{coldest['city_name']} ({coldest['state']})",
)
col3.metric(
    "💧 Umidade Média",
    f"{avg_humidity:.0f}%",
    f"{len(df_latest)} capitais filtradas",
)
col4.metric(
    "🌧️ Maior Chuva (1h)",
    f"{rainiest['rain_1h']:.2f} mm",
    f"{rainiest['city_name']} ({rainiest['state']})",
)
col5.metric(
    "🗄️ Registros Carregados",
    f"{len(df_all)}",
    f"Última: {df_latest['datetime'].max().strftime('%H:%M')}",
)

st.divider()

# --- Abas do Dashboard ---
tab_overview, tab_climate, tab_history = st.tabs(
    [
        "🗺️ Mapa & Comparativo Atual",
        "📊 Regiões & Correlações",
        "📈 Histórico & Tabela de Dados",
    ]
)

with tab_overview:
    left_col, right_col = st.columns([1.05, 1.0])

    with left_col:
        st.subheader("Mapa Meteorológico em Tempo Real")
        fig_map = px.scatter_map(
            df_latest,
            lat="latitude",
            lon="longitude",
            color="temperature",
            size="humidity",
            size_max=24,
            hover_name="city_name",
            hover_data={
                "state": True,
                "region": True,
                "temperature": ":.1f",
                "feels_like": ":.1f",
                "humidity": True,
                "weather_description": True,
                "rain_1h": ":.2f",
                "wind_speed": ":.1f",
                "latitude": False,
                "longitude": False,
            },
            color_continuous_scale="RdYlBu_r",
            zoom=3.1,
            center={"lat": -14.2, "lon": -51.9},
            map_style="carto-positron",
            height=470,
        )
        fig_map.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0})
        st.plotly_chart(fig_map, width="stretch")

    with right_col:
        st.subheader("Temperatura Real vs. Sensação Térmica (°C)")
        df_bar = df_latest.sort_values("temperature", ascending=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                y=df_bar["city_name"],
                x=df_bar["temperature"],
                name="Temperatura (°C)",
                orientation="h",
                marker_color="#f97316",
                text=df_bar["temperature"].map(lambda v: f"{v:.1f}°C"),
                textposition="auto",
            )
        )
        fig_bar.add_trace(
            go.Bar(
                y=df_bar["city_name"],
                x=df_bar["feels_like"],
                name="Sensação Térmica (°C)",
                orientation="h",
                marker_color="#38bdf8",
                text=df_bar["feels_like"].map(lambda v: f"{v:.1f}°C"),
                textposition="auto",
            )
        )
        fig_bar.update_layout(
            barmode="group",
            height=470,
            xaxis_title="Graus Celsius (°C)",
            yaxis_title="",
            legend={"orientation": "h", "y": 1.08},
            margin={"r": 10, "t": 30, "l": 10, "b": 10},
        )
        st.plotly_chart(fig_bar, width="stretch")

with tab_climate:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Temperatura × Umidade (Tamanho = Vento m/s)")
        fig_scatter = px.scatter(
            df_latest,
            x="temperature",
            y="humidity",
            color="region",
            size=df_latest["wind_speed"].clip(lower=0.5),
            text="state",
            hover_name="city_name",
            hover_data=["weather_description", "wind_speed", "rain_1h"],
            labels={
                "temperature": "Temperatura (°C)",
                "humidity": "Umidade Relativa (%)",
                "region": "Região",
            },
            height=420,
        )
        fig_scatter.update_traces(textposition="top center")
        st.plotly_chart(fig_scatter, width="stretch")

    with c2:
        st.subheader("Temperatura Média por Região Brasileira")
        df_reg = (
            df_latest.groupby("region", as_index=False)
            .agg(
                temp_media=("temperature", "mean"),
                umidade_media=("humidity", "mean"),
            )
            .sort_values("temp_media", ascending=False)
        )
        fig_reg = px.bar(
            df_reg,
            x="region",
            y="temp_media",
            color="region",
            text=df_reg["temp_media"].map(lambda v: f"{v:.1f} °C"),
            labels={"region": "Região", "temp_media": "Temperatura Média (°C)"},
            height=420,
        )
        fig_reg.update_traces(textposition="outside")
        fig_reg.update_layout(showlegend=False)
        st.plotly_chart(fig_reg, width="stretch")

with tab_history:
    st.subheader("Evolução das Coletas (Série Temporal)")
    fig_line = px.line(
        df_filtered.sort_values("datetime"),
        x="datetime",
        y="temperature",
        color="city_name",
        markers=True,
        labels={
            "datetime": "Data/Hora (Horário de Brasília)",
            "temperature": "Temperatura (°C)",
            "city_name": "Capital",
        },
        height=380,
    )
    st.plotly_chart(fig_line, width="stretch")

    st.subheader("Registros Meteorológicos Estruturados")
    display_cols = [
        "datetime",
        "city_name",
        "state",
        "region",
        "weather_description",
        "temperature",
        "feels_like",
        "humidity",
        "rain_1h",
        "wind_speed",
        "pressure",
    ]
    st.dataframe(df_filtered[display_cols], width="stretch", hide_index=True)

    csv_bytes = df_filtered[display_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv_bytes,
        file_name="weather_data_brasil.csv",
        mime="text/csv",
    )

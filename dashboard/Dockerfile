FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    streamlit \
    plotly \
    pandas \
    pyarrow \
    sqlalchemy \
    psycopg2-binary \
    python-dotenv \
    requests

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]


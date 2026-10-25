FROM apache/airflow:3.1.7

USER airflow
RUN pip install --no-cache-dir "pandas<3" pyarrow python-dotenv


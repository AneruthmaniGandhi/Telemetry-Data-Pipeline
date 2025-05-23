FROM apache/airflow:2.9.3
USER root
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir apache-airflow-providers-fab apache-airflow-providers-openlineage>=1.8.0 
FROM apache/airflow:2.10.5

USER root

# Install Docker CLI so BashOperator can call `docker exec` on the Spark container
COPY --from=docker:24.0-cli /usr/local/bin/docker /usr/local/bin/docker

# Create docker group (GID 999 is standard on Linux/WSL2) and add airflow user
RUN groupadd --gid 999 docker 2>/dev/null || true \
    && usermod -aG docker airflow

USER airflow

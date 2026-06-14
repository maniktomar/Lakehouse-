FROM apache/spark:3.5.3

USER root

RUN mkdir -p /opt/spark/ivy /tmp/iceberg-ivy \
    && chown -R 185:0 /opt/spark/ivy /tmp/iceberg-ivy

USER 185

ENV PATH="/opt/spark/bin:${PATH}"
ENV ICEBERG_VERSION=1.8.1
ENV NESSIE_VERSION=0.102.5
ENV SPARK_PACKAGES=org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:${ICEBERG_VERSION},org.apache.iceberg:iceberg-aws-bundle:${ICEBERG_VERSION},org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:${NESSIE_VERSION}

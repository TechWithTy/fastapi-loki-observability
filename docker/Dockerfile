# Loki & Alloy Multi-Stage Dockerfile
# This Dockerfile can be used to build either a Loki or Alloy container for custom deployments,
# or as a reference for local testing, CI/CD, or extending with extra tools/plugins.
#
# Usage:
#   docker build -t my-loki -f Dockerfile --target loki .
#   docker build -t my-alloy -f Dockerfile --target alloy .
#
# For most production uses, prefer the official images in docker-compose, but this file
# is useful for custom builds, local testing, or CI/CD pipelines.

############################
# Loki Stage
############################
FROM grafana/loki:latest AS loki
LABEL maintainer="YourTeam <your@email.com>"
WORKDIR /etc/loki

# Copy in example config if present (for local/test only)
COPY loki-local-config.yaml ./loki-local-config.yaml

# Expose Loki port (configurable via env)
EXPOSE 3100

# Environment variables for secrets/config (override at runtime)
ENV LOKI_AUTH_ENABLED=${LOKI_AUTH_ENABLED:-false}
ENV LOKI_ADMIN_API_ENABLED=${LOKI_ADMIN_API_ENABLED:-false}
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV S3_BUCKET_NAME=${S3_BUCKET_NAME}
ENV CERT_FILE=${CERT_FILE:-/etc/ssl/certs/server.crt}
ENV KEY_FILE=${KEY_FILE:-/etc/ssl/private/server.key}
ENV CA_FILE=${CA_FILE:-/etc/ssl/certs/ca.crt}
ENV LOKI_RETENTION_PERIOD=${LOKI_RETENTION_PERIOD:-168h}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --spider --quiet http://localhost:3100/ready || exit 1

# Use example config if present, fallback to default
CMD ["sh", "-c", "if [ -f /etc/loki/loki-local-config.yaml ]; then exec /usr/bin/loki -config.file=/etc/loki/loki-local-config.yaml; else exec /usr/bin/loki -config.file=/etc/loki/local-config.yaml; fi"]

############################
# * Alloy Stage
############################
FROM grafana/alloy:latest AS alloy
LABEL maintainer="YourTeam <your@email.com>"
WORKDIR /etc/alloy

# Copy in example config if present (for local/test only)
COPY alloy-config.example ./alloy-config.example

# Environment variables for secrets/config (override at runtime)
ENV ALLOY_LOKI_ENDPOINT=${ALLOY_LOKI_ENDPOINT:-http://loki:3100/loki/api/v1/push}
ENV CERT_FILE=${CERT_FILE:-/etc/ssl/certs/server.crt}
ENV KEY_FILE=${KEY_FILE:-/etc/ssl/private/server.key}
ENV CA_FILE=${CA_FILE:-/etc/ssl/certs/ca.crt}
ENV ALLOY_RETENTION_PERIOD=${ALLOY_RETENTION_PERIOD:-168h}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD pgrep alloy || exit 1

# Use example config if present, fallback to default
CMD ["sh", "-c", "if [ -f /etc/alloy/alloy-config.example ]; then exec /usr/bin/alloy --config.file=/etc/alloy/alloy-config.example; else exec /usr/bin/alloy --config.file=/etc/alloy/config.alloy; fi"]

############################
# OpenTelemetry Collector Stage
############################
FROM otel/opentelemetry-collector-contrib:latest AS otelcol
LABEL maintainer="YourTeam <your@email.com>"
WORKDIR /etc/otelcol

# Copy in example config if present (for local/test only)
COPY otel-collector-config.example.yaml ./otel-collector-config.example.yaml

# Environment variables for secrets/config (override at runtime)
ENV OTEL_LOKI_ENDPOINT=${OTEL_LOKI_ENDPOINT:-http://loki:3100/loki/api/v1/push}
ENV OTEL_LOKI_TENANT_ID=${OTEL_LOKI_TENANT_ID}
ENV CERT_FILE=${CERT_FILE:-/etc/ssl/certs/server.crt}
ENV KEY_FILE=${KEY_FILE:-/etc/ssl/private/server.key}
ENV CA_FILE=${CA_FILE:-/etc/ssl/certs/ca.crt}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD pgrep otelcol || exit 1

# Use example config if present, fallback to default
CMD ["sh", "-c", "if [ -f /etc/otelcol/otel-collector-config.example.yaml ]; then exec /otelcol --config=/etc/otelcol/otel-collector-config.example.yaml; else exec /otelcol --config=/etc/otelcol/config.yaml; fi"]

############################
# Tempo Stage (Optional)
############################
FROM grafana/tempo:latest AS tempo
LABEL maintainer="YourTeam <your@email.com>"
WORKDIR /etc/tempo

# Copy in example config if present (for local/test only)
COPY tempo-config.example.yaml ./tempo-config.example.yaml

# Environment variables for secrets/config (override at runtime)
#  ! Uncomment the following section to use Tempo configuration

# ENV TEMPO_PORT=${TEMPO_PORT:-3200}
# ENV TEMPO_OTLP_PORT=${TEMPO_OTLP_PORT:-4317}
# ENV TEMPO_STORAGE_PATH=${TEMPO_STORAGE_PATH:-/var/tempo}
# ENV TEMPO_RETENTION_PERIOD=${TEMPO_RETENTION_PERIOD:-168h}
# ENV TEMPO_RECEIVER_JAEGER_PORT=${TEMPO_RECEIVER_JAEGER_PORT:-14250}
# ENV TEMPO_ZIPKIN_PORT=${TEMPO_ZIPKIN_PORT:-9411}

# # Expose configurable ports
# EXPOSE ${TEMPO_PORT} ${TEMPO_OTLP_PORT} ${TEMPO_RECEIVER_JAEGER_PORT} ${TEMPO_ZIPKIN_PORT}

# # Healthcheck for Tempo
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#   CMD wget --spider --quiet http://localhost:${TEMPO_PORT}/ready || exit 1

# # Use example config if present, fallback to default
# CMD ["sh", "-c", "if [ -f /etc/tempo/tempo-config.example.yaml ]; then exec tempo -config.file=/etc/tempo/tempo-config.example.yaml; else exec tempo -config.file=/etc/tempo/tempo.yaml; fi"]

############################
# Usage Notes
############################
# - For SSL/TLS, mount certs/keys at runtime and set CERT_FILE, KEY_FILE, CA_FILE env vars.
# - For log retention/TTL, set LOKI_RETENTION_PERIOD or ALLOY_RETENTION_PERIOD via env or config file.
# - Example configs are for local/test only; override with production configs via volume mounts.
# - NEVER hardcode secrets in the Dockerfile. Use env vars or Docker secrets.
# - See https://grafana.com/docs/loki/latest/ and https://grafana.com/docs/alloy/latest/ for config options.
# - For production, mount configuration files and use secrets managers for sensitive data.
# - For OpenTelemetry Collector, mount your own config for production; example is for local/test.
# - Use OTEL_LOKI_ENDPOINT, OTEL_LOKI_TENANT_ID, CERT_FILE, KEY_FILE, CA_FILE as env vars for secure config.
# - See https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/lokiexporter for docs.

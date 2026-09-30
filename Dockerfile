FROM python:3.11-slim
LABEL maintainer="dsugurtuna"

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "hla_investigator"]
CMD ["--help"]

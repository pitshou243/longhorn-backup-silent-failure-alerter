FROM python:3.12-alpine
WORKDIR /app
RUN addgroup -S exporter && adduser -S exporter -G exporter
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/exporter.py ./exporter.py
USER exporter
EXPOSE 9501
ENTRYPOINT ["python", "/app/exporter.py"]

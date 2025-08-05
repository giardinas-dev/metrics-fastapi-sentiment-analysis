from fastapi import FastAPI, Request
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
# Modello dati in ingresso
from pydantic import BaseModel
app = FastAPI()

# --- Metriche Prometheus
metrics_received = Counter("metrics_received_total", "Totale metriche ricevute")
sentiment_counter = Counter("sentiment_count", "Conteggio sentiment", ["sentiment"])
value_histogram = Histogram("value_distribution", "Distribuzione valori", ["sentiment"])

# Endpoint Prometheus per esportare metriche
@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


class MetricData(BaseModel):
    sentiment: str
    value: float

@app.post("/metrics")
async def receive_metrics(data: MetricData):
    metrics_received.inc()
    sentiment_counter.labels(sentiment=data.sentiment).inc()
    value_histogram.labels(sentiment=data.sentiment).observe(data.value)
    return {"message": "Metric received"}

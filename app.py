from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from fastapi.responses import JSONResponse

app = FastAPI()

# Memorizzazione temporanea delle metriche in RAM
metrics_store = {
    "metrics_received_total": 0,
    "sentiment_count": {
        "positive": 0,
        "neutral": 0,
        "negative": 0
    },
    "value_distribution_sum": {
        "positive": 0.0,
        "neutral": 0.0,
        "negative": 0.0
    },
    "value_distribution_count": {
        "positive": 0,
        "neutral": 0,
        "negative": 0
    }
}

class MetricData(BaseModel):
    sentiment: str
    value: float

@app.post("/metrics")
async def receive_metrics(data: MetricData):
    sentiment = data.sentiment.lower()
    value = data.value

    metrics_store["metrics_received_total"] += 1

    if sentiment not in metrics_store["sentiment_count"]:
        # Se il sentiment non esiste, inizializzalo
        metrics_store["sentiment_count"][sentiment] = 0
        metrics_store["value_distribution_sum"][sentiment] = 0.0
        metrics_store["value_distribution_count"][sentiment] = 0

    metrics_store["sentiment_count"][sentiment] += 1
    metrics_store["value_distribution_sum"][sentiment] += value
    metrics_store["value_distribution_count"][sentiment] += 1

    return {"message": "Metric received"}

@app.get("/metrics-json")
async def get_metrics_json():
    return JSONResponse(content=metrics_store)

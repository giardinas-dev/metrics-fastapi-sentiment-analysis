from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import threading

app = FastAPI()

# Memorizzazione temporanea delle metriche
metrics_store = {
    "metrics_received_total": 0,
    "sentiment_count": {},
    "value_distribution_sum": {},
    "value_distribution_count": {},
    "text_length_sum": {},
    "timestamps": {}  # nuovo: lista di datetime per ogni sentiment
}

class MetricData(BaseModel):
    sentiment: str
    value: float
    text: str

@app.post("/metrics")
async def receive_metrics(data: MetricData):
    sentiment = data.sentiment.lower()
    value = data.value
    text_length = len(data.text)
    timestamp = datetime.utcnow()

    metrics_store["metrics_received_total"] += 1

    # Inizializza se nuovo sentiment
    if sentiment not in metrics_store["sentiment_count"]:
        metrics_store["sentiment_count"][sentiment] = 0
        metrics_store["value_distribution_sum"][sentiment] = 0.0
        metrics_store["value_distribution_count"][sentiment] = 0
        metrics_store["text_length_sum"][sentiment] = 0
        metrics_store["timestamps"][sentiment] = []

    metrics_store["sentiment_count"][sentiment] += 1
    metrics_store["value_distribution_sum"][sentiment] += value
    metrics_store["value_distribution_count"][sentiment] += 1
    metrics_store["text_length_sum"][sentiment] += text_length
    metrics_store["timestamps"][sentiment].append(timestamp)

    return {"message": "Metric received"}

@app.get("/metrics_data")
async def get_metrics_json():
    sentiments = []
    counts = []
    lengths = []

    now = datetime.utcnow()

    for sentiment in metrics_store["sentiment_count"]:
        # Filtra metriche più vecchie di 3 giorni
        timestamps = metrics_store["timestamps"][sentiment]
        cutoff = now - timedelta(days=3)
        recent_timestamps = [t for t in timestamps if t >= cutoff]
        old_count = len(timestamps) - len(recent_timestamps)

        # Aggiorna le metriche eliminando vecchie metriche
        metrics_store["sentiment_count"][sentiment] -= old_count
        metrics_store["value_distribution_count"][sentiment] -= old_count
        metrics_store["text_length_sum"][sentiment] -= old_count * (
            metrics_store["text_length_sum"][sentiment] / max(len(timestamps),1)
        )
        metrics_store["timestamps"][sentiment] = recent_timestamps

        count = metrics_store["sentiment_count"][sentiment]
        value_sum = metrics_store["value_distribution_sum"].get(sentiment, 0.0)
        value_count = metrics_store["value_distribution_count"].get(sentiment, 0)
        length_sum = metrics_store["text_length_sum"].get(sentiment, 0)

        value_avg = value_sum / value_count if value_count > 0 else 0.0
        text_length_avg = length_sum / value_count if value_count > 0 else 0.0

        sentiments.append({
            "label": sentiment,
            "count": count,
            "value_avg": round(value_avg, 4),
            "text_length_avg": round(text_length_avg, 2),
            "timestamps": [t.isoformat() for t in recent_timestamps]
        })

        counts.append(count)
        lengths.append(text_length_avg)

    # Normalizzazione min-max
    count_min, count_max = min(counts) if counts else 0, max(counts) if counts else 1
    length_min, length_max = min(lengths) if lengths else 0, max(lengths) if lengths else 1

    for s in sentiments:
        # Normalizza count
        s["count_norm"] = (
            (s["count"] - count_min) / (count_max - count_min)
            if count_max != count_min else 1.0
        )
        # Normalizza text_length_avg
        s["text_length_norm"] = (
            (s["text_length_avg"] - length_min) / (length_max - length_min)
            if length_max != length_min else 1.0
        )

    return JSONResponse(content=sentiments)

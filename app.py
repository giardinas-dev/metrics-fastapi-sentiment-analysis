from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()

# Memorizzazione temporanea metriche in RAM
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
    },
    "text_length_sum": {
        "positive": 0,
        "neutral": 0,
        "negative": 0
    }
}

class MetricData(BaseModel):
    sentiment: str
    value: float
    text: str  # aggiungo testo per lunghezza

@app.post("/metrics")
async def receive_metrics(data: MetricData):
    sentiment = data.sentiment.lower()
    value = data.value
    text_length = len(data.text)

    metrics_store["metrics_received_total"] += 1

    # Inizializzo se nuovo sentiment
    if sentiment not in metrics_store["sentiment_count"]:
        metrics_store["sentiment_count"][sentiment] = 0
        metrics_store["value_distribution_sum"][sentiment] = 0.0
        metrics_store["value_distribution_count"][sentiment] = 0
        metrics_store["text_length_sum"][sentiment] = 0

    metrics_store["sentiment_count"][sentiment] += 1
    metrics_store["value_distribution_sum"][sentiment] += value
    metrics_store["value_distribution_count"][sentiment] += 1
    metrics_store["text_length_sum"][sentiment] += text_length

    return {"message": "Metric received"}

@app.get("/metrics-json")
async def get_metrics_json():
    avg_values = {}
    avg_lengths = {}

    for sentiment in metrics_store["value_distribution_sum"]:
        count = metrics_store["value_distribution_count"].get(sentiment, 0)
        if count > 0:
            avg_values[sentiment] = metrics_store["value_distribution_sum"][sentiment] / count
            avg_lengths[sentiment] = metrics_store["text_length_sum"][sentiment] / count
        else:
            avg_values[sentiment] = 0.0
            avg_lengths[sentiment] = 0.0

    output = {
        "metrics_received_total": metrics_store["metrics_received_total"],
        "sentiment_count": metrics_store["sentiment_count"],
        "value_distribution_avg": avg_values,
        "text_length_avg": avg_lengths
    }

    return JSONResponse(content=output)

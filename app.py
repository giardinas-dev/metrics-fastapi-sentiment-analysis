from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()

# Memorizzazione temporanea delle metriche
metrics_store = {
    "metrics_received_total": 0,
    "sentiment_count": {},
    "value_distribution_sum": {},
    "value_distribution_count": {},
    "text_length_sum": {}
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

    metrics_store["metrics_received_total"] += 1

    # Inizializza se nuovo sentiment
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

@app.get("/metrics_data")
async def get_metrics_json():
    sentiments = []

    for sentiment in metrics_store["sentiment_count"]:
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
            "text_length_avg": round(text_length_avg, 2)
        })

    output = {
        "metrics_received_total": metrics_store["metrics_received_total"],
        "sentiments": sentiments
    }

    return JSONResponse(content=output)

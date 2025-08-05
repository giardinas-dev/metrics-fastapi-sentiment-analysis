from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import time
from collections import defaultdict, deque

app = FastAPI()

class MetricData(BaseModel):
    sentiment: str
    value: float
    text: str = ""

# Memorizziamo metriche ultime 24h in una deque
metrics_history = deque()

# Conteggi e somme per aggregati
count_by_sentiment = defaultdict(int)
sum_by_sentiment = defaultdict(float)
total_received = 0

def clean_old_metrics():
    cutoff = time.time() - 86400
    while metrics_history and metrics_history[0][0] < cutoff:
        ts, sent, val, txt_len = metrics_history.popleft()
        count_by_sentiment[sent] -= 1
        sum_by_sentiment[sent] -= val

@app.post("/metrics")
def receive_metrics(data: MetricData):
    global total_received
    now = time.time()

    # Pulisce metriche vecchie
    clean_old_metrics()

    # Aggiunge metrica nuova
    metrics_history.append((now, data.sentiment, data.value, len(data.text)))

    # Aggiorna aggregati
    count_by_sentiment[data.sentiment] += 1
    sum_by_sentiment[data.sentiment] += data.value
    total_received += 1

    return {"message": "Metric received"}

@app.get("/metrics")
def get_metrics():
    # Pulisce metriche vecchie
    clean_old_metrics()

    avg_by_sentiment = {}
    for sent in count_by_sentiment:
        if count_by_sentiment[sent] > 0:
            avg_by_sentiment[sent] = sum_by_sentiment[sent] / count_by_sentiment[sent]
        else:
            avg_by_sentiment[sent] = 0.0

    result = {
        "total_metrics_received": total_received,
        "count_by_sentiment": dict(count_by_sentiment),
        "avg_value_by_sentiment": avg_by_sentiment,
        "metrics_last_24h": [
            {"timestamp": ts, "sentiment": sent, "value": val, "text_length": txt_len}
            for ts, sent, val, txt_len in list(metrics_history)
        ],
    }
    return JSONResponse(content=result)

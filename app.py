from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict, deque

app = FastAPI()

# --- Modello dati in ingresso
class MetricData(BaseModel):
    sentiment: str
    value: float
    text: str = ""  # opzionale, se vuoi metriche sul testo

# --- Storage metriche ultime 24h
# Uso deque per efficienza, salva tuple: (timestamp, sentiment, value, text_length)
metrics_history = deque()

# --- Variabili di supporto per metriche aggregate
metrics_count_by_sentiment = defaultdict(int)
metrics_total_received = 0
metrics_values_by_sentiment = defaultdict(list)

# Lock per sincronizzare accesso
lock = asyncio.Lock()

# --- Funzione per pulire metriche più vecchie di 24h
def clean_old_metrics():
    cutoff = time.time() - 86400
    while metrics_history and metrics_history[0][0] < cutoff:
        ts, sent, val, txt_len = metrics_history.popleft()
        metrics_count_by_sentiment[sent] -= 1
        metrics_values_by_sentiment[sent].remove(val)

@app.post("/metrics")
async def receive_metrics(data: MetricData):
    global metrics_total_received
    now = time.time()

    async with lock:
        # Pulizia metriche vecchie
        clean_old_metrics()

        # Salva metrica nuova
        metrics_history.append((now, data.sentiment, data.value, len(data.text)))

        # Aggiorna aggregati
        metrics_count_by_sentiment[data.sentiment] += 1
        metrics_values_by_sentiment[data.sentiment].append(data.value)
        metrics_total_received += 1

    return {"message": "Metric received"}

@app.get("/metrics")
async def get_metrics():
    async with lock:
        # Pulizia metriche vecchie
        clean_old_metrics()

        # Prepara dati aggregati per grafana
        result = {
            "total_metrics_received": metrics_total_received,
            "count_by_sentiment": dict(metrics_count_by_sentiment),
            "avg_value_by_sentiment": {},
            "metrics_last_24h": [
                {
                    "timestamp": ts,
                    "sentiment": sent,
                    "value": val,
                    "text_length": txt_len,
                }
                for ts, sent, val, txt_len in list(metrics_history)
            ],
        }

        # Calcolo medie per sentiment
        for sent, values in metrics_values_by_sentiment.items():
            if values:
                result["avg_value_by_sentiment"][sent] = sum(values) / len(values)
            else:
                result["avg_value_by_sentiment"][sent] = 0.0

    return JSONResponse(content=result)

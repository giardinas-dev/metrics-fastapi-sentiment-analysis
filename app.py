from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import time

app = FastAPI()

class MetricData(BaseModel):
    sentiment: str
    value: float

# Lista che salva metriche come tuple (timestamp, sentiment, value)
metrics_history = []

@app.post("/metrics")
async def receive_metrics(data: MetricData):
    now = time.time()
    metrics_history.append((now, data.sentiment, data.value))
    # Pulisci metriche più vecchie di 24h (86400 secondi)
    cutoff = now - 86400
    while metrics_history and metrics_history[0][0] < cutoff:
        metrics_history.pop(0)
    return {"message": "Metric received"}

@app.get("/metrics")
async def get_metrics():
    # Filtra metriche ultime 24h
    now = time.time()
    cutoff = now - 86400
    recent_metrics = [m for m in metrics_history if m[0] >= cutoff]
    
    # Puoi restituire in formato JSON
    return JSONResponse(content={"metrics": recent_metrics})

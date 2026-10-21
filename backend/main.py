
from fastapi import FastAPI

app = FastAPI(
    title="Housefull API",
    description="Seat booking and event management API",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Housefull!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

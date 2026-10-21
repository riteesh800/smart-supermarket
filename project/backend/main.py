"""
FastAPI main application
AI-Driven Smart Supermarket System — Portable Edition
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import init_db
from routes import inventory, sales, customers, ml, suppliers, upload, chatbot

app = FastAPI(
    title="Smart Supermarket API",
    description="AI-Driven Inventory, Demand Forecasting & Customer Intelligence — Works with any dataset",
    version="3.0.0"
)

# CORS for frontend (configurable via CORS_ORIGINS)
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
cors_origins = [o.strip() for o in cors_origins_raw.split(",")] if cors_origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routes
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(customers.router)
app.include_router(ml.router)
app.include_router(suppliers.router)
app.include_router(upload.router)
app.include_router(chatbot.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Smart Supermarket API v3 — Portable Edition", "docs": "/docs"}

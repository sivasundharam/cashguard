import os

import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

_client: AsyncIOMotorClient = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
    return _client


def get_db():
    return get_client()["cashguard"]


def invoices_col():
    return get_db()["invoices"]


def client_profiles_col():
    return get_db()["client_profiles"]


def collections_cases_col():
    return get_db()["collections_cases"]


def forecast_snapshots_col():
    return get_db()["forecast_snapshots"]

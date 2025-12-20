import httpx
import streamlit as st
import json
from pathlib import Path
import time

HONOR_ROLL_FILE = Path("data/honor_roll_2025.json")

@st.cache_data
def fetch_user_id(callsign: str) -> str | None:
    url = f"https://sotl.as/api/activators/{callsign}"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json().get("userId")
    except httpx.HTTPError:
        return None

def fetch_activations(user_id: str, year: int = 2025) -> list:

    url = f"https://api-db2.sota.org.uk/logs/activator/{user_id}/{year}/99999/"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return []

def fetch_honor_roll() -> list:
    url = "https://api-db2.sota.org.uk/rolls/activator/-1/2025/all/all"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        sanitized_data = []

        for entry in data:
            sanitized_entry = entry.copy()
            sanitized_entry.pop("Username", None)
            sanitized_data.append(sanitized_entry)

        # Save to disk
        HONOR_ROLL_FILE.parent.mkdir(exist_ok=True)
        with open(HONOR_ROLL_FILE, "w", encoding="utf-8") as f:
            json.dump(sanitized_data, f, indent=2)

        return data

    except httpx.HTTPError:
        return []

def fetch_summit_elevation(summit_code: str) -> int:

    url = f"https://api-db2.sota.org.uk/api/summits/{summit_code}"

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        elevation = data.get("altM", 0)
        time.sleep(0.05) # so we don't hammer the API
        return elevation

    except httpx.HTTPError:
        return 0
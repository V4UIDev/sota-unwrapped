from collections import Counter
from datetime import datetime
import json
import pandas as pd
from pathlib import Path
from services.api import fetch_summit_elevation

HONOR_ROLL_FILE = Path("data/honor_roll_2025.json")

def get_points_total(activation_data):

    max_total_activation = max(
    activation_data,
    key=lambda a: a["Total"]
    )

    return max_total_activation["Total"]

def get_most_qsos_activation(activation_data):

    most_qsos_activation = max(
        activation_data,
        key=lambda a: a["QSOs"]
    )

    return most_qsos_activation

def count_activations(activation_data):

    return len(activation_data)

def most_popular_month_with_season(activation_data):
    # Extract months from activation dates
    months = []
    for activation in activation_data:
        date_str = activation.get("ActivationDate")
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            months.append(date_obj)

    if not months:
        return None, None, 0  # No data

    # Count occurrences of each month
    month_counts = Counter([m.strftime("%B %Y") for m in months])
    most_common_month_str, count = month_counts.most_common(1)[0]

    # Determine season based on month number
    month_number = datetime.strptime(most_common_month_str, "%B %Y").month
    if month_number in [5, 6, 7, 8]:
        season = "Summer"
    elif month_number in [12, 1, 2]:
        season = "Winter"
    else:
        season = "Awesome"

    return most_common_month_str, season, count

def get_percentile_bucket(user_total_points):

    with open(HONOR_ROLL_FILE, "r", encoding="utf-8") as f:
        honor_roll = json.load(f)

    # Extract and sort all total points (descending)
    totals = sorted(
        [u["totalPoints"] for u in honor_roll if "totalPoints" in u],
        reverse=True
    )

    if not totals:
        return None, "No data"

    total_users = len(totals)

    # Find how many users have MORE points than this user
    users_above = sum(1 for t in totals if t > user_total_points)

    # Percentile rank (e.g. top 10%)
    percentile = (users_above / total_users) * 100

    # Bucket logic
    if percentile <= 10:
        bucket = "Top 10%"
    elif percentile <= 20:
        bucket = "Top 20%"
    elif percentile <= 30:
        bucket = "Top 30%"
    elif percentile <= 50:
        bucket = "Top 50%"
    else:
        bucket = "Below Top 50%"

    return round(percentile, 1), bucket

def get_total_elevation_gain(activation_data: list) -> int:
    total_elevation = 0

    for activation in activation_data:
        summit_code = activation.get("SummitCode")
        if not summit_code:
            continue

        elevation = fetch_summit_elevation(summit_code)
        total_elevation += elevation

    return total_elevation

def get_qsos_per_band(activation_data):
    band_keys = ["QSO160","QSO80","QSO60","QSO40","QSO30","QSO20",
                 "QSO17","QSO15","QSO12","QSO10","QSO6","QSO4","QSO2",
                 "QSO70c","QSO23c"]

    # Map keys to human-readable names
    band_map = {}
    for band in band_keys:
        if band.endswith("c"):
            band_map[band] = band.replace("QSO","").replace("c","cm")
        else:
            band_map[band] = band.replace("QSO","") + "m"

    # Initialize totals
    band_totals = {name: 0 for name in band_map.values()}

    # Sum QSOs across activations
    for act in activation_data:
        for band, band_name in band_map.items():
            band_totals[band_name] += act.get(band, 0)

    # Convert to DataFrame
    df = pd.DataFrame({
        "Band": list(band_totals.keys()),
        "QSOs": list(band_totals.values())
    })

    # Filter out zero QSOs
    df = df[df["QSOs"] > 0].reset_index(drop=True)

    # Correct order
    band_order = ["160m","80m","60m","40m","30m","20m","17m","15m",
                  "12m","10m","6m","4m","2m","70cm","23cm"]
    df["Band"] = pd.Categorical(df["Band"], categories=band_order, ordered=True)
    df = df.sort_values("Band").reset_index(drop=True)

    if not df.empty:
        most_popular_row = df.loc[df["QSOs"].idxmax()]
        most_popular_band = most_popular_row["Band"]
        most_popular_band_qsos = int(most_popular_row["QSOs"])
    else:
        most_popular_band = None
        most_popular_band_qsos = 0

    return df, most_popular_band, most_popular_band_qsos

def get_qso_stats(activation_data):
    qso_total = 0
    activation_count = 0

    for activation in activation_data:
        qsos = activation.get("QSOs")
        if qsos is None:
            continue  # skip malformed entries

        qso_total += qsos
        activation_count += 1

    average_qsos = round(
    qso_total / activation_count, 2
)

    return qso_total, average_qsos
import streamlit as st
import altair as alt
import pandas as pd
import base64
import time
import streamlit.components.v1 as components
import io
from services.api import fetch_user_id, fetch_activations, fetch_honor_roll
from services.data import (
    get_points_total,
    get_most_qsos_activation,
    count_activations,
    most_popular_month_with_season,
    get_percentile_bucket,
    get_total_elevation_gain,
    get_qsos_per_band,
    get_qso_stats
)

with open("data/logo.png", "rb") as f:
    logo = f.read()

b64_logo = base64.b64encode(logo).decode()

st.set_page_config(page_title="SOTA Unwrapped 2025", layout="centered")

# -----------------------------
# Cache API calls
# -----------------------------
@st.cache_data(show_spinner=False)
def fetch_user_id_cached(callsign):
    return fetch_user_id(callsign)

@st.cache_data(show_spinner=False)
def fetch_activations_cached(user_id):
    return fetch_activations(user_id)

@st.cache_data(show_spinner=False)
def fetch_honor_roll_cached():
    return fetch_honor_roll()

# -----------------------------
# Cache computation functions
# -----------------------------
@st.cache_data(show_spinner=False)
def get_total_points_cached(activation_data):
    return get_points_total(activation_data)

@st.cache_data(show_spinner=False)
def get_most_qsos_cached(activation_data):
    return get_most_qsos_activation(activation_data)

@st.cache_data(show_spinner=False)
def get_total_elevation_cached(activation_data):
    return get_total_elevation_gain(activation_data)

@st.cache_data(show_spinner=False)
def get_qsos_per_band_cached(activation_data):
    return get_qsos_per_band(activation_data)

@st.cache_data(show_spinner=False)
def get_qso_stats_cached(activation_data):
    return get_qso_stats(activation_data)

# -----------------------------
# Session state
# -----------------------------
if "callsign" not in st.session_state:
    st.session_state.callsign = None
if "slide" not in st.session_state:
    st.session_state.slide = 0
if "burst_done" not in st.session_state:
    st.session_state.burst_done = set()

# -----------------------------
# Slide navigation
# -----------------------------
def next_slide():
    if st.session_state.slide < len(slides) - 1:
        st.session_state.slide += 1

def prev_slide():
    if st.session_state.slide > 0:
        st.session_state.slide -= 1

# -----------------------------
# Callsign input
# -----------------------------
if st.session_state.callsign is None:
    st.title("Your 2025 SOTA Unwrapped 🎧🏔️")
    st.write("Enter your callsign to begin:")

    callsign_input = st.text_input("Callsign", placeholder="e.g. G5JFJ")
    if st.button("Start Unwrapping ▶") and callsign_input:
        st.session_state.callsign = callsign_input.upper()
        st.rerun()

    st.stop()

callsign = st.session_state.callsign

# -----------------------------
# Fetch user data
# -----------------------------
user_id = fetch_user_id_cached(callsign)
activation_data = fetch_activations_cached(user_id)

# Precompute metrics
total_points = get_total_points_cached(activation_data)
most_qsos_activation = get_most_qsos_cached(activation_data)
num_activations = count_activations(activation_data)
popular_month, season, activations_count = most_popular_month_with_season(activation_data)
percentile, bucket = get_percentile_bucket(total_points)
total_vertical = get_total_elevation_cached(activation_data)
qsos_df, most_popular_band, most_popular_band_qsos = get_qsos_per_band_cached(activation_data)
qso_total, average_qsos_per_activation = get_qso_stats_cached(activation_data)

# -----------------------------
# Slides content
# -----------------------------
slides = [
    {
        "title": f"{callsign}'s 2025 SOTA Unwrapped ✨",
        "type": "metric",
        "metric": "Total Points",
        "value": total_points,
        "emoji": "🏆",
        "color": "#1DB954",
        "description": f"You did {num_activations} activations this year!"
    },
    {
        "title": "Highest QSO Activation 📡",
        "type": "metric",
        "metric": most_qsos_activation["Summit"],
        "value": most_qsos_activation["QSOs"],
        "emoji": "⚡",
        "color": "#FF6F61",
        "description": "QSOs made on this summit!"
    },
    {
        "title": "Total QSOs 📡",
        "type": "metric",
        "metric": "Total QSOs this year",
        "value": qso_total,
        "emoji": "🗣️",
        "color": "#7B3FE4",
        "description": f"Average {average_qsos_per_activation:.2f} QSOs per activation!"
    },
    {
        "title": "Your Busiest Month 📆",
        "type": "metric",
        "metric": popular_month,
        "value": f"{activations_count} activations",
        "emoji": "🌞" if season=="Summer" else "❄️" if season=="Winter" else "🌄",
        "color": "#FFA500",
        "description": f"{season} vibes for your activations!"
    },
    {
        "title": "QSOs per Band 📶",
        "type": "chart",
        "chart_data": qsos_df,
        "description": "Here’s how your QSOs were distributed across bands!"
    },
    {
        "title": "Percentile & Rank 🙌",
        "type": "metric",
        "metric": f"{bucket} percentile",
        "value": f"{percentile:.1f}%",
        "emoji": "🙌",
        "color": "#FFD700",
        "description": "Compared to all activators"
    },
    {
        "title": "Total Vertical of all Summits 🏔️",
        "type": "metric",
        "metric": "Vertical Gain",
        "value": total_vertical,
        "emoji": "⛰️",
        "color": "#00BFFF",
        "description": "Reach for the stars!"
    },
    {
        "title": "Your Favourite Band 🥁",
        "type": "metric",
        "metric": f"it accounted for {most_popular_band_qsos} QSOs!",
        "value": f"{most_popular_band}",
        "emoji": "🤘",
        "color": "#00A8A8",
        "description": "Yeah, not that type of band.."
    },
    {
    "title": "Your SOTA Unwrapped",
    "type": "share"
    },
]

# -----------------------------
# Display current slide
# -----------------------------
slide = slides[st.session_state.slide]
st.markdown(f"### {slide['title']}")

if slide["type"] == "chart":
    st.write(slide["description"])
    placeholder = st.empty()
    chart_data = slide["chart_data"].copy()
    steps = 50
    x_max = chart_data["QSOs"].max()
    chart_data["QSOsAnimated"] = 0

    for i in range(1, steps + 1):
        chart_data["QSOsAnimated"] = (chart_data["QSOs"] * i / steps).astype(int)
        chart = alt.Chart(chart_data).mark_bar(color="#FF6F61").encode(
            x=alt.X("QSOsAnimated:Q", title="Number of QSOs", scale=alt.Scale(domain=[0, x_max])),
            y=alt.Y("Band:N", sort="-x", title="Band")
        ).properties(height=400)
        placeholder.altair_chart(chart, width='stretch')
        time.sleep(0.02)

elif slide["type"] == "metric":
    with st.container():

        # Animate Vertical Gain / Total Activations
        if slide["metric"] in ["Vertical Gain", "Total Points"]:
            placeholder = st.empty()
            steps = 40
            for i in range(steps + 1):
                display_value = int(i * slide["value"] / steps)
                if slide["metric"] == "Vertical Gain":
                    display_value = f"{display_value:,}m"
                else:
                    display_value = f"{display_value:,}"
                placeholder.markdown(
                    f"""
                    <div class="fade-in-card" style="
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    font-family: 'Inter', Arial, Helvetica, sans-serif;
                    background-color:{slide['color']};
                    padding: 20px 30px;
                    border-radius: 20px;
                    text-align: center;
                    color: white;
                    width: 100%;
                    max-width: 600px;
                    margin: auto;
                ">
                    <h1 style="font-size:60px; margin:0;">
                        {slide['emoji']} {display_value}
                    </h1>
                    <p style="font-size:24px; margin:4px 0 0 0;">
                        {slide['metric']}
                    </p>
                    <p style="font-size:18px; margin-top:10px;">
                        {slide['description']}
                    </p>
                </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(0.03)
        else:
            # Fade-in card
            components.html(f"""
            <div class="fade-in-card" style="
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: 'Inter', Arial, Helvetica, sans-serif;
                background-color:{slide['color']};
                padding: 20px 30px;
                border-radius: 20px;
                text-align: center;
                color: white;
                width: 100%;
                max-width: 600px;
                margin: auto;
            ">
                <h1 style="font-size:60px; margin:0;">
                    {slide['emoji']} {slide['value']}
                </h1>
                <p style="font-size:24px; margin:4px 0 0 0;">
                    {slide['metric']}
                </p>
                <p style="font-size:18px; margin-top:10px;">
                    {slide['description']}
                </p>
            </div>

            <style>
            @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
            }}

            .fade-in-card {{
                animation: fadeInUp 0.8s ease-out;
            }}
            </style>
            """, height=250)

elif slide["type"] == "share":

    components.html(
        f"""
        <div style="
            max-width: 420px;
            margin: 40px auto;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            padding: 28px;
            border-radius: 24px;
            color: white;
            text-align: center;
            font-family: system-ui, -apple-system, BlinkMacSystemFont;
        ">

            <img src="data:image/png;base64,{b64_logo}"
                style="width:90px; margin-bottom:14px;" />

            <h2 style="margin: 6px 0 20px 0;">
                {callsign}
            </h2>

            <div style="
                display:grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-bottom: 20px;
            ">

                <div>
                    <h3>📶 Favourite Band</h3>
                    <p>{most_popular_band}</p>
                </div>

                <div>
                    <h3>📡 Total QSOs</h3>
                    <p>{qso_total}</p>
                </div>

                <div>
                    <h3>🏆 Total Points</h3>
                    <p>{total_points}</p>
                </div>

                <div>
                    <h3>🏔️ Total Activations</h3>
                    <p>{num_activations}</p>
                </div>

            </div>

            <p style="opacity:0.85; font-size:14px;">
                SOTA Unwrapped 2025
            </p>

        </div>
        """,
        height=560
    )


# -----------------------------
# Navigation buttons
# -----------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.session_state.slide > 0:
        st.button("⬅ Previous", on_click=prev_slide)
with col3:
    if st.session_state.slide < len(slides) - 1:
        st.button("Next ➡", on_click=next_slide)

# Progress bar
st.progress((st.session_state.slide + 1) / len(slides))

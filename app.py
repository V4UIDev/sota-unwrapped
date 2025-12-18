import streamlit as st
import altair as alt
import pandas as pd
import time
from services.api import fetch_user_id, fetch_activations, fetch_honor_roll
from services.data import (
    get_points_total,
    get_most_qsos_activation,
    count_activations,
    most_popular_month_with_season,
    get_percentile_bucket,
    get_total_elevation_gain,
    get_qsos_per_band
)

st.set_page_config(page_title="SOTA Wrapped 2025", layout="centered")

year = 2025

# -----------------------------
# Caching API calls
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
# Caching computation functions
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

# -----------------------------
# Session state initialization
# -----------------------------
if "callsign" not in st.session_state:
    st.session_state.callsign = None
if "slide" not in st.session_state:
    st.session_state.slide = 0  # current slide index

# -----------------------------
# Slide navigation
# -----------------------------
def next_slide():
    st.session_state.slide += 1

def prev_slide():
    st.session_state.slide -= 1

# -----------------------------
# Callsign input
# -----------------------------
if st.session_state.callsign is None:
    st.title("Your 2025 SOTA Wrapped 🎧🏔️")
    st.write("Enter your callsign to begin:")

    callsign_input = st.text_input("Callsign", placeholder="e.g. G5JFJ")
    if st.button("Start Wrapped ▶") and callsign_input:
        st.session_state.callsign = callsign_input.upper()
        st.rerun()

    st.stop()

callsign = st.session_state.callsign

# -----------------------------
# Fetch user data (cached)
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
qsos_df = get_qsos_per_band_cached(activation_data)

# # -----------------------------
# # Animated metric helper (for activations & vertical only)
# # -----------------------------
# def animated_metric(value, duration=1.5):
#     placeholder = st.empty()
#     steps = 50
#     sleep_time = duration / steps
#     for i in range(steps + 1):
#         display_value = int(i * value / steps)
#         placeholder.markdown(f"<h1 style='font-size:60px; text-align:center;'>{display_value:,}m</h1>"
#                                <p style="font-size:24px;">{slide['metric']}</p>
#                               <p style="font-size:18px; margin-top:10px;">{slide['description']}</p>
#     </div>, unsafe_allow_html=True)
#         time.sleep(sleep_time)

# -----------------------------
# Slides content
# -----------------------------
slides = [
    {
        "title": f"{callsign}'s 2025 SOTA Wrapped ✨",
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
        "description": f"QSOs made on this summit!"
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
        "title": "Total Vertical Climbed 🏔️",
        "type": "metric",
        "metric": "Vertical Gain",
        "value": total_vertical,
        "emoji": "⛰️",
        "color": "#00BFFF",
        "description": "Reach for the stars!"
    },
]

# -----------------------------
# Display current slide
# -----------------------------
slide = slides[st.session_state.slide]

st.markdown(f"### {slide['title']}")

if slide["type"] == "chart":
    st.markdown(f"### {slide['title']}")
    st.write(slide["description"])

    placeholder = st.empty()
    chart_data = slide["chart_data"].copy()
    steps = 50
    duration = 1.5
    sleep_time = duration / steps

    # Get fixed max for x-axis
    x_max = chart_data["QSOs"].max()

    # Initialize animated column
    chart_data["QSOsAnimated"] = 0

    for i in range(1, steps + 1):
        chart_data["QSOsAnimated"] = (chart_data["QSOs"] * i / steps).astype(int)
        chart = alt.Chart(chart_data).mark_bar(color="#FF6F61").encode(
            x=alt.X("QSOsAnimated:Q", title="Number of QSOs", scale=alt.Scale(domain=[0, x_max])),
            y=alt.Y("Band:N", sort="-x", title="Band")
        ).properties(height=400)
        placeholder.altair_chart(chart, use_container_width=True)
        sleep_time = sleep_time / 1.05
        time.sleep(sleep_time)

elif slide["type"] == "metric":
    with st.container():
        # Animate only for Vertical Gain and Total Activations
        if slide["title"] == "Total Vertical Climbed 🏔️":
            placeholder = st.empty()
            steps = 50
            duration = 1.5
            sleep_time = duration / steps
            for i in range(steps + 1):
                display_value = int(i * slide["value"] / steps)
                placeholder.markdown(
                    f"""
                    <div style="background-color:{slide['color']}; padding:40px; border-radius:20px; text-align:center; color:white;">
                        <h1 style="font-size:60px;">{slide['emoji']} {display_value:,}m</h1>
                        <p style="font-size:24px;">{slide['metric']}</p>
                        <p style="font-size:18px; margin-top:10px;">{slide['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(sleep_time)
        else:
            # Static card for other metrics
            st.markdown(
                f"""
                <div style="background-color:{slide['color']}; padding:40px; border-radius:20px; text-align:center; color:white;">
                    <h1 style="font-size:60px;">{slide['emoji']} {slide['value']}</h1>
                    <p style="font-size:24px;">{slide['metric']}</p>
                    <p style="font-size:18px; margin-top:10px;">{slide['description']}</p>
                </div>
                """,
                unsafe_allow_html=True
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

# -----------------------------
# Progress indicator
# -----------------------------
st.progress((st.session_state.slide + 1) / len(slides))

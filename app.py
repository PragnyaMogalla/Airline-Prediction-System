import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import os

st.set_page_config(
    page_title="FlightOps | Big Data Analytics Engine",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# STYLING & MODERN GLASSMORPHISM UI
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        padding: 26px 32px;
        border-radius: 16px;
        margin-bottom: 22px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .pipeline-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.25);
        border: 1px solid rgba(129, 140, 248, 0.4);
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #c7d2fe;
        margin-top: 10px;
    }

    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 14px 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Full readable name mapping
CARRIER_NAMES = {
    "9E": "Endeavor Air (9E)",
    "AA": "American Airlines (AA)",
    "AS": "Alaska Airlines (AS)",
    "B6": "JetBlue Airways (B6)",
    "CO": "Continental Airlines (CO)",
    "DL": "Delta Air Lines (DL)",
    "EV": "ExpressJet Airlines (EV)",
    "F9": "Frontier Airlines (F9)",
    "FL": "AirTran Airways (FL)",
    "HA": "Hawaiian Airlines (HA)",
    "MQ": "Envoy Air (MQ)",
    "NW": "Northwest Airlines (NW)",
    "OH": "PSA Airlines (OH)",
    "OO": "SkyWest Airlines (OO)",
    "UA": "United Airlines (UA)",
    "US": "US Airways (US)",
    "WN": "Southwest Airlines (WN)",
    "XE": "ExpressJet / JSX (XE)",
    "YV": "Mesa Airlines (YV)"
}

# ---------------------------------------------------------
# FAST DATA ACCESS LAYER
# ---------------------------------------------------------
@st.cache_data
def fetch_cassandra_data():
    csv_path = "carrier_metrics.csv"
    tsv_path = "mapreduce_output.tsv"
    cols = ["carrier", "total_flights", "total_delay_min", "avg_delay_min", "total_cancelled", "cancellation_rate"]
    
    # 1. Fast direct local check
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 100:
        try:
            return pd.read_csv(csv_path, names=cols)
        except Exception:
            pass

    # 2. Query Cassandra container via CQLSH
    cmd = [
        "docker", "exec", "cassandra_db", "cqlsh", "-e",
        "SELECT carrier, total_flights, total_delay_min, avg_delay_min, total_cancelled, cancellation_rate FROM airline_analytics.carrier_metrics;"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        
        records = []
        for line in lines:
            if line.startswith("carrier") or line.startswith("---") or line.startswith("(") or not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 6:
                try:
                    records.append({
                        "carrier": parts[0],
                        "total_flights": int(parts[1]),
                        "total_delay_min": float(parts[2]),
                        "avg_delay_min": float(parts[3]),
                        "total_cancelled": int(parts[4]),
                        "cancellation_rate": float(parts[5])
                    })
                except ValueError:
                    continue
        if records:
            return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Failed to query Apache Cassandra: {e}")

    # 3. TSV Fallback
    if os.path.exists(tsv_path) and os.path.getsize(tsv_path) > 100:
        try:
            return pd.read_csv(tsv_path, sep="\t", names=cols)
        except Exception:
            pass

    return pd.DataFrame()

df = fetch_cassandra_data()

if df.empty:
    st.error("No records found in Cassandra. Please ensure MapReduce output is loaded.")
    st.stop()

# Clean dataframe and apply names
df = df[df["carrier"].str.match(r"^[A-Z0-9]{2}$", na=False)].reset_index(drop=True)
df["carrier_name"] = df["carrier"].map(lambda c: CARRIER_NAMES.get(c, f"Airline {c}"))

# ---------------------------------------------------------
# HERO HEADER
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #ffffff;">✈️ FlightOps Big Data Analytics Engine</h1>
    <p style="margin: 6px 0 0 0; color: #cbd5e1; font-size: 1rem;">
        Real-time risk scoring directly backed by distributed MapReduce batch aggregations in Apache Cassandra.
    </p>
    <div class="pipeline-badge">
        HDFS &bull; Hadoop MapReduce (6.4M Records) &bull; Apache Cassandra &bull; Streamlit
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SECTION 1: SYSTEM KPI METRICS
# ---------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Airlines Evaluated", f"{len(df)} Carriers")
c2.metric("Total Flights Analyzed", f"{int(df['total_flights'].sum()):,}")
c3.metric("Worst Average Delay", f"{df['avg_delay_min'].max():.1f} min", delta=f"{df.sort_values('avg_delay_min', ascending=False).iloc[0]['carrier']}", delta_color="inverse")
c4.metric("Avg Cancellation Rate", f"{df['cancellation_rate'].mean():.2f}%")

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# SECTION 2: INTERACTIVE CHARTS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    fig_delay = px.bar(
        df.sort_values(by="avg_delay_min", ascending=False),
        x="carrier",
        y="avg_delay_min",
        hover_data=["carrier_name", "total_flights"],
        color="avg_delay_min",
        color_continuous_scale="sunsetdark",
        title="<b>Average Departure Delay per Airline (Minutes)</b>"
    )
    fig_delay.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Airline Carrier",
        yaxis_title="Minutes",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_delay, width="stretch")

with col2:
    fig_cancel = px.bar(
        df.sort_values(by="cancellation_rate", ascending=False),
        x="carrier",
        y="cancellation_rate",
        hover_data=["carrier_name", "total_cancelled"],
        color="cancellation_rate",
        color_continuous_scale="burg",
        title="<b>Cancellation Probability Rate (%)</b>"
    )
    fig_cancel.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Airline Carrier",
        yaxis_title="Cancellation Rate (%)",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_cancel, width="stretch")

st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.08); margin: 28px 0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# SECTION 3: REAL-TIME RISK PREDICTOR & BENCHMARK PRESETS
# ---------------------------------------------------------
st.markdown("### 🔮 Real-Time Flight Risk & On-Time Predictor")
st.markdown("Move any slider or change any value below — risk scores recompute **instantaneously**:")

# Default session state initialization (Widget keys use karenge)
if "carrier_select" not in st.session_state:
    st.session_state.carrier_select = "WN" if "WN" in df["carrier"].values else df["carrier"].iloc[0]
if "day_select" not in st.session_state:
    st.session_state.day_select = "Friday"
if "hour_slider" not in st.session_state:
    st.session_state.hour_slider = 18
if "dist_input" not in st.session_state:
    st.session_state.dist_input = 650

# Benchmark Preset Buttons
b_col1, b_col2, b_col3 = st.columns(3)

with b_col1:
    if st.button("🟢 Scenario A: Best-Case (High On-Time)", use_container_width=True):
        best_carrier = "HA" if "HA" in df["carrier"].values else df.sort_values("avg_delay_min").iloc[0]["carrier"]
        st.session_state.carrier_select = best_carrier
        st.session_state.day_select = "Tuesday"
        st.session_state.hour_slider = 11
        st.session_state.dist_input = 2500
        st.rerun()

with b_col2:
    if st.button("🔴 Scenario B: Worst-Case (High Delay Risk)", use_container_width=True):
        worst_carrier = "EV" if "EV" in df["carrier"].values else df.sort_values("avg_delay_min", ascending=False).iloc[0]["carrier"]
        st.session_state.carrier_select = worst_carrier
        st.session_state.day_select = "Friday"
        st.session_state.hour_slider = 19
        st.session_state.dist_input = 180
        st.rerun()

with b_col3:
    if st.button("🔄 Reset Parameters", use_container_width=True):
        st.session_state.carrier_select = df["carrier"].iloc[0]
        st.session_state.day_select = "Wednesday"
        st.session_state.hour_slider = 14
        st.session_state.dist_input = 750
        st.rerun()

# Dynamic Input Row (Direct session_state se sync honge)
p1, p2, p3, p4 = st.columns(4)

with p1:
    carrier_list = df["carrier"].tolist()
    selected_carrier = st.selectbox(
        "Operating Carrier",
        options=carrier_list,
        format_func=lambda x: CARRIER_NAMES.get(x, x),
        key="carrier_select"
    )

with p2:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_day = st.selectbox(
        "Departure Day",
        options=days,
        key="day_select"
    )

with p3:
    selected_hour = st.slider(
        "Scheduled Departure Hour (24h)",
        min_value=0,
        max_value=23,
        key="hour_slider"
    )

with p4:
    selected_distance = st.number_input(
        "Flight Distance (Miles)",
        min_value=50,
        max_value=5000,
        step=50,
        key="dist_input"
    )

# Instant calculation logic
row = df[df["carrier"] == selected_carrier].iloc[0]
base_delay = row["avg_delay_min"]
base_cancel = row["cancellation_rate"]

time_factor = 1.65 if 16 <= selected_hour <= 21 else (1.15 if 6 <= selected_hour <= 9 else 0.80)
day_factor = 1.35 if selected_day in ["Friday", "Sunday"] else 0.90
dist_factor = 1.25 if selected_distance < 400 else 0.90

if base_delay <= 0:
    pred_delay = round(base_delay + (selected_hour * 0.15), 1)
else:
    pred_delay = round(base_delay * time_factor * day_factor * dist_factor, 1)

pred_cancel = round(min(base_cancel * (time_factor if time_factor > 1 else 1.0) * (day_factor if day_factor > 1 else 1.0), 100.0), 2)

# Instant Metrics Display
st.markdown("#### 📊 Live Risk Assessment")
r1, r2, r3 = st.columns(3)
r1.metric("Predicted Departure Delay", f"{pred_delay} min", delta=f"{pred_delay - base_delay:+.1f} min vs carrier avg", delta_color="inverse")
r2.metric("Estimated Cancellation Chance", f"{pred_cancel}%", delta=f"{pred_cancel - base_cancel:+.2f}% vs carrier avg", delta_color="inverse")

with r3:
    if pred_delay < 15:
        st.success("### 🟢 High On-Time Reliability\nMinimal delay probability expected.")
    elif pred_delay <= 28:
        st.warning("### 🟡 Moderate Operational Risk\nBuffer advised for connecting flights.")
    else:
        st.error("### 🔴 High Delay Probability\nCongested route window detected.")

# ---------------------------------------------------------
# SECTION 4: LIVE CASSANDRA RAW RECORDS
# ---------------------------------------------------------
st.markdown("### 🗄️ Apache Cassandra Staged Table")
st.dataframe(
    df[["carrier", "carrier_name", "total_flights", "total_delay_min", "avg_delay_min", "total_cancelled", "cancellation_rate"]],
    column_config={
        "carrier": "Code",
        "carrier_name": "Airline Name",
        "total_flights": st.column_config.NumberColumn("Total Flights", format="%d"),
        "total_delay_min": st.column_config.NumberColumn("Total Delay (min)", format="%.0f"),
        "avg_delay_min": st.column_config.NumberColumn("Avg Delay (min)", format="%.2f"),
        "total_cancelled": st.column_config.NumberColumn("Cancellations", format="%d"),
        "cancellation_rate": st.column_config.ProgressColumn("Cancel Rate (%)", format="%.2f%%", min_value=0, max_value=5),
    },
    hide_index=True,
    width="stretch"
)

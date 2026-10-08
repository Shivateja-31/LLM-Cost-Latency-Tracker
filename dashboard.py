import sqlite3

import pandas as pd
import streamlit as st


DB_NAME = "llm_metrics.db"


# Page Configuration

st.set_page_config(
    page_title="LLM Cost & Latency Tracker",
    page_icon="📊",
    layout="wide"
)


# Load Data

@st.cache_data
def load_metrics():

    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query(
        "SELECT * FROM llm_requests",
        conn
    )

    conn.close()

    return df


# Title

st.title("📊 LLM Cost & Latency Tracker")

st.write(
    "Monitor LLM requests, token usage, "
    "latency, model usage, and cost."
)


# Load Database

try:

    df = load_metrics()

except Exception as e:

    st.error(
        "Could not load the database."
    )

    st.code(str(e))

    st.stop()


# Empty Database

if df.empty:

    st.warning(
        "No LLM requests recorded yet."
    )

    st.info(
        "Run tracker.py first to create "
        "some LLM requests."
    )

    st.stop()


# Convert Timestamp

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)


# Sidebar Filters

st.sidebar.header("Filters")


models = sorted(
    df["model"].dropna().unique()
)


selected_models = st.sidebar.multiselect(
    "Models",
    models,
    default=models
)


statuses = sorted(
    df["status"].dropna().unique()
)


selected_statuses = st.sidebar.multiselect(
    "Status",
    statuses,
    default=statuses
)


filtered_df = df[
    df["model"].isin(selected_models)
    & df["status"].isin(selected_statuses)
]


if filtered_df.empty:

    st.warning(
        "No requests match the selected filters."
    )

    st.stop()


# Key Metrics

total_requests = len(filtered_df)

total_tokens = int(
    filtered_df["total_tokens"].sum()
)

total_cost = filtered_df["cost"].sum()

average_latency = filtered_df[
    "latency_ms"
].mean()

average_tokens = filtered_df[
    "total_tokens"
].mean()


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Requests",
    total_requests
)


col2.metric(
    "Total Tokens",
    f"{total_tokens:,}"
)


col3.metric(
    "Total Cost",
    f"${total_cost:.6f}"
)


col4.metric(
    "Avg Latency",
    f"{average_latency / 1000:.1f} seconds"
)


# Token Metrics

st.subheader("Token Usage")


col1, col2, col3 = st.columns(3)


col1.metric(
    "Prompt Tokens",
    f"{int(filtered_df['prompt_tokens'].sum()):,}"
)


col2.metric(
    "Completion Tokens",
    f"{int(filtered_df['completion_tokens'].sum()):,}"
)


col3.metric(
    "Average Tokens / Request",
    f"{average_tokens:.0f}"
)


# Latency Chart

st.subheader("Latency Over Time")


latency_df = (
    filtered_df
    .sort_values("timestamp")
    .set_index("timestamp")
)


st.line_chart(
    latency_df["latency_ms"]
)


# Model Usage

st.subheader("Model Usage")


model_usage = (
    filtered_df["model"]
    .value_counts()
)


st.bar_chart(
    model_usage
)


# Token Usage by Model

st.subheader("Token Usage by Model")


token_usage = (
    filtered_df
    .groupby("model")["total_tokens"]
    .sum()
    .sort_values(ascending=False)
)


st.bar_chart(
    token_usage
)


# Cost by Model

st.subheader("Cost by Model")


cost_by_model = (
    filtered_df
    .groupby("model")["cost"]
    .sum()
    .sort_values(ascending=False)
)


st.bar_chart(
    cost_by_model
)


# Slowest Requests

st.subheader("🐌 Slowest Requests")


slowest = (
    filtered_df
    .sort_values(
        "latency_ms",
        ascending=False
    )
    .head(10)
)


st.dataframe(
    slowest[
        [
            "timestamp",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "latency_ms",
            "cost",
            "status"
        ]
    ],
    use_container_width=True
)


# Most Expensive Requests

st.subheader("💰 Most Expensive Requests")


expensive = (
    filtered_df
    .sort_values(
        "cost",
        ascending=False
    )
    .head(10)
)


st.dataframe(
    expensive[
        [
            "timestamp",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "latency_ms",
            "cost",
            "status"
        ]
    ],
    use_container_width=True
)


# Request History

st.subheader("Request History")


st.dataframe(
    filtered_df.sort_values(
        "timestamp",
        ascending=False
    ),
    use_container_width=True
)


# Request Details

st.subheader("Request Details")


request_id = st.selectbox(
    "Select a request",
    filtered_df["id"].tolist()
)


selected_request = filtered_df[
    filtered_df["id"] == request_id
].iloc[0]


st.markdown("### Prompt")

st.code(
    selected_request["prompt"],
    language="text"
)


st.markdown("### Response")

st.code(
    selected_request["response"],
    language="text"
)


# Refresh

if st.button("🔄 Refresh Dashboard"):

    st.cache_data.clear()

    st.rerun()
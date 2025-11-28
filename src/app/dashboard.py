"""
BTC Sentiment Index Dashboard

A Streamlit-based web interface that displays Bitcoin sentiment analysis
by consuming FastAPI endpoints. Features include KPI cards, trend charts,
gauge visualization, and top sentiment drivers.
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ============================================================================
# Configuration
# ============================================================================

# FastAPI base URL (update this if your API runs on a different host/port)
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="BTC Sentiment Index",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# API Client Functions
# ============================================================================

def fetch_sentiment_index(granularity: str = "daily", days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Fetch sentiment index data from the FastAPI endpoint.
    
    Args:
        granularity: Time granularity ('hourly' or 'daily')
        days: Number of days to fetch
        
    Returns:
        Response data dict or None if request fails
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/sentiment/",
            params={"granularity": granularity, "days": days},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch sentiment index: {e}")
        return None


def fetch_top_drivers(day: str) -> Optional[Dict[str, Any]]:
    """
    Fetch top sentiment drivers for a specific day.
    
    Args:
        day: Date in YYYY-MM-DD format
        
    Returns:
        Response data dict or None if request fails
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/drivers/",
            params={"day": day},
            timeout=10
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch top drivers: {e}")
        return None


def check_api_health() -> bool:
    """
    Check if the FastAPI service is healthy and reachable.
    
    Returns:
        True if API is healthy, False otherwise
    """
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health/", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# ============================================================================
# Visualization Functions
# ============================================================================

def create_sentiment_chart(data: List[Dict[str, Any]], granularity: str) -> go.Figure:
    """
    Create a Plotly line chart showing sentiment trend over time.
    
    Args:
        data: List of sentiment data points
        granularity: Time granularity for x-axis formatting
        
    Returns:
        Plotly figure object
    """
    if not data:
        return go.Figure()
    
    # Extract data
    timestamps = [point["ts"] for point in data]
    raw_values = [point["raw"] for point in data]
    smoothed_values = [point["smoothed"] for point in data]
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    
    # Add raw sentiment line (lighter, thinner)
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=raw_values,
            name="Raw Sentiment",
            line=dict(color="rgba(99, 110, 250, 0.3)", width=1),
            mode="lines"
        )
    )
    
    # Add smoothed sentiment line (prominent)
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=smoothed_values,
            name="Smoothed Sentiment",
            line=dict(color="rgb(99, 110, 250)", width=3),
            mode="lines"
        )
    )
    
    # Add zero reference line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="Neutral"
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"30-Day Sentiment Trend ({granularity.capitalize()})",
            x=0.5,
            xanchor="center"
        ),
        xaxis_title="Date",
        yaxis_title="Sentiment Score",
        hovermode="x unified",
        template="plotly_white",
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Set y-axis range to -1 to 1
    fig.update_yaxes(range=[-1, 1], tickformat=".2f")
    
    return fig


def create_gauge_chart(current_value: float) -> go.Figure:
    """
    Create a Plotly gauge chart showing current sentiment index.
    
    Args:
        current_value: Current sentiment score (-1 to 1)
        
    Returns:
        Plotly figure object
    """
    # Determine color based on sentiment
    if current_value < -0.3:
        color = "red"
    elif current_value < 0.3:
        color = "yellow"
    else:
        color = "green"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Current Sentiment", 'font': {'size': 24}},
        delta={'reference': 0, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-1, -0.3], 'color': 'rgba(255, 0, 0, 0.2)'},
                {'range': [-0.3, 0.3], 'color': 'rgba(255, 255, 0, 0.2)'},
                {'range': [0.3, 1], 'color': 'rgba(0, 255, 0, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': current_value
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    """Main dashboard application."""
    
    # Header
    st.title("₿ BTC Sentiment Index (Beta)")
    st.markdown("Real-time Bitcoin sentiment analysis from news and social media")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Unable to connect to the API service. Please ensure the FastAPI server is running on http://localhost:8000")
        st.info("Start the API server with: `uvicorn src.api.main:app --reload`")
        st.stop()
    
    # ========================================================================
    # Sidebar Controls
    # ========================================================================
    
    st.sidebar.header("⚙️ Settings")
    
    # Granularity selector
    granularity = st.sidebar.selectbox(
        "Data Granularity",
        options=["daily", "hourly"],
        index=0,
        help="Select the time granularity for sentiment data"
    )
    
    # Days selector
    days = st.sidebar.slider(
        "Days to Display",
        min_value=7,
        max_value=180,
        value=30 if granularity == "daily" else 7,
        step=1,
        help="Number of days to show in the trend chart"
    )
    
    # Date selector for top drivers
    driver_date = st.sidebar.date_input(
        "Top Drivers Date",
        value=datetime.now().date(),
        max_value=datetime.now().date(),
        help="Select a date to view top sentiment drivers"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This dashboard analyzes Bitcoin sentiment from multiple sources including "
        "news articles and Reddit posts. Sentiment scores range from -1 (very negative) "
        "to +1 (very positive)."
    )
    
    # ========================================================================
    # Fetch Data
    # ========================================================================
    
    with st.spinner("Loading sentiment data..."):
        sentiment_data = fetch_sentiment_index(granularity=granularity, days=days)
    
    if not sentiment_data or not sentiment_data.get("data"):
        st.warning("No sentiment data available for the selected period.")
        st.stop()
    
    data_points = sentiment_data["data"]
    
    # ========================================================================
    # KPI Cards
    # ========================================================================
    
    st.markdown("### 📊 Key Metrics")
    
    # Calculate metrics
    current_smoothed = data_points[-1]["smoothed"] if data_points else 0.0
    current_raw = data_points[-1]["raw"] if data_points else 0.0
    
    # Calculate 24h delta (last vs previous day)
    delta_24h = 0
    if len(data_points) >= 2:
        if granularity == "daily":
            delta_24h = data_points[-1]["smoothed"] - data_points[-2]["smoothed"]
        else:
            # For hourly, get ~24 hours ago (24 data points)
            lookback = min(24, len(data_points) - 1)
            delta_24h = data_points[-1]["smoothed"] - data_points[-lookback]["smoothed"]
    
    # Calculate 7d delta
    delta_7d = 0
    if len(data_points) >= 7:
        if granularity == "daily":
            lookback = min(7, len(data_points) - 1)
        else:
            lookback = min(7 * 24, len(data_points) - 1)
        delta_7d = data_points[-1]["smoothed"] - data_points[-lookback]["smoothed"]
    
    # Display KPI cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Current Sentiment",
            value=f"{current_smoothed:.3f}",
            delta=None,
            help="Smoothed sentiment score (-1 to +1)"
        )
    
    with col2:
        st.metric(
            label="Raw Sentiment",
            value=f"{current_raw:.3f}",
            delta=None,
            help="Unsmoothed sentiment score"
        )
    
    with col3:
        st.metric(
            label="24h Change",
            value=f"{delta_24h:+.3f}",
            delta=None,
            help="Change in sentiment over the last 24 hours"
        )
    
    with col4:
        st.metric(
            label="7d Change",
            value=f"{delta_7d:+.3f}",
            delta=None,
            help="Change in sentiment over the last 7 days"
        )
    
    st.markdown("---")
    
    # ========================================================================
    # Visualizations
    # ========================================================================
    
    # Create two columns for chart and gauge
    viz_col1, viz_col2 = st.columns([2, 1])
    
    with viz_col1:
        st.markdown("### 📈 Sentiment Trend")
        trend_chart = create_sentiment_chart(data_points, granularity)
        # Constrain x-axis to the selected range window
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        trend_chart.update_xaxes(range=[start_dt, end_dt])
        st.plotly_chart(trend_chart, use_container_width=True)
    
    with viz_col2:
        st.markdown("### 🎯 Current Index")
        gauge_chart = create_gauge_chart(current_smoothed)
        st.plotly_chart(gauge_chart, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # Top Drivers
    # ========================================================================
    
    st.markdown("### 🔥 Top Sentiment Drivers")
    st.caption(f"Showing top drivers for {driver_date.strftime('%Y-%m-%d')}")
    
    with st.spinner("Loading top drivers..."):
        drivers_data = fetch_top_drivers(driver_date.strftime("%Y-%m-%d"))
    
    if not drivers_data:
        st.info(f"No driver data available for {driver_date.strftime('%Y-%m-%d')}. Try selecting a different date.")
    else:
        # Create two columns for positive and negative drivers
        pos_col, neg_col = st.columns(2)
        
        with pos_col:
            st.markdown("#### 🟢 Most Positive")
            positives = drivers_data.get("positives", [])
            
            if not positives:
                st.info("No positive drivers found")
            else:
                for i, driver in enumerate(positives, 1):
                    with st.container():
                        # Create a colored box for each driver
                        sentiment_color = "green"
                        st.markdown(
                            f"""
                            <div style="padding: 10px; margin: 5px 0; border-left: 4px solid {sentiment_color}; background-color: rgba(0, 255, 0, 0.05);">
                                <strong>{i}. <a href="{driver['url']}" target="_blank">{driver['title']}</a></strong><br>
                                <small>Sentiment: <code>{driver['polarity']:.3f}</code> | Source: {driver['source']}</small>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        
        with neg_col:
            st.markdown("#### 🔴 Most Negative")
            negatives = drivers_data.get("negatives", [])
            
            if not negatives:
                st.info("No negative drivers found")
            else:
                for i, driver in enumerate(negatives, 1):
                    with st.container():
                        sentiment_color = "red"
                        st.markdown(
                            f"""
                            <div style="padding: 10px; margin: 5px 0; border-left: 4px solid {sentiment_color}; background-color: rgba(255, 0, 0, 0.05);">
                                <strong>{i}. <a href="{driver['url']}" target="_blank">{driver['title']}</a></strong><br>
                                <small>Sentiment: <code>{driver['polarity']:.3f}</code> | Source: {driver['source']}</small>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
    
    # ========================================================================
    # Footer
    # ========================================================================
    
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray; padding: 20px;">
            <small>BTC Sentiment Analysis Dashboard | Data updated in real-time | 
            <a href="http://localhost:8000/docs" target="_blank">API Documentation</a></small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

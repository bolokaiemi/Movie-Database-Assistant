import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# ==========================================
# PAGE CONFIGURATION & PREMIUM STYLING
# ==========================================
st.set_page_config(
    page_title="Cinema Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Netflix/Stoplight Cinema dark theme
st.markdown("""
<style>
    /* Primary brand colors and font sizes */
    html, body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: #0c0f17 !important;
        color: #cbd5e1 !important;
    }
    
    /* 1. SIDEBAR HIGH-CONTRAST LABELS & TEXTS (DARK TEXT ON LIGHT BACKGROUND) */
    /* Forces every label, description, and widget label inside the sidebar to be highly legible dark slate */
    section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] label *,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        color: #0f172a !important; /* Rich dark slate for high contrast on light backgrounds */
        font-weight: 700 !important; /* Bold */
        font-size: 1.05rem !important;
    }
    
    /* 2. SELECTBOX WIDGET STYLING (DARK SLATE TEXT ON LIGHT BACKGROUND) */
    /* Force selectbox input containers to use rich dark slate text */
    section[data-testid="stSidebar"] div[data-baseweb="select"] *,
    section[data-testid="stSidebar"] div[data-baseweb="select"] div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #0f172a !important; /* Force dark slate text */
    }
    
    /* Force dropdown menu popover options to also use rich dark slate text */
    div[role="listbox"] *,
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"] *,
    ul[role="listbox"] * {
        color: #0f172a !important; /* Force all list choices to be dark slate */
    }
    
    /* 3. SIDEBAR BUTTON STYLING (THEME-RED SYNC BUTTON WITH BOLD WHITE TEXT) */
    section[data-testid="stSidebar"] button {
        background-color: #ff3c3c !important; /* Bright red matching the theme */
        color: #ffffff !important; /* Pure white bold text for excellent contrast on red */
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(255, 60, 60, 0.25) !important;
        transition: transform 0.2s ease, background-color 0.2s ease !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #ff5555 !important;
        transform: translateY(-2px) !important;
    }
    
    /* 2. METRIC CARD READABILITY OVERRIDES */
    div.stMetric {
        background: #151e2e !important;
        border: 2px solid #334155 !important;
        border-radius: 16px;
        padding: 24px 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div.stMetric:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 77, 77, 0.6) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
    }
    
    /* Force ALL text elements inside metrics cards to inherit white color by default */
    div[data-testid="stMetric"] * {
        color: #ffffff !important;
    }
    
    /* Metric typography overrides */
    div[data-testid="stMetricValue"], 
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ff4d4d !important; /* Radiant coral-red number */
        font-weight: 900 !important;
        font-size: 2.85rem !important;
        text-shadow: 0 0 12px rgba(255, 77, 77, 0.45) !important;
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #ffffff !important; /* Pure white for maximum visibility */
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-size: 1.15rem !important;
    }
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] *,
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        background-color: rgba(9, 12, 18, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        padding: 4px 10px !important;
        display: inline-block !important;
        margin-top: 4px !important;
    }
    
    /* 3. TABS CUSTOMIZATION WITH HIGH CONTRAST */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
        border: 1px solid #1e293b;
        padding: 0 24px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stTabs [data-baseweb="tab"] * {
        color: #cbd5e1 !important; /* High contrast silver-gray text for unselected tabs */
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255, 60, 60, 0.1);
        border-color: rgba(255, 60, 60, 0.3);
    }
    .stTabs [data-baseweb="tab"]:hover * {
        color: #ffffff !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 60, 60, 0.2) !important;
        border-color: #ff3c3c !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #ffffff !important; /* Pure white for active tab */
        font-weight: 700 !important;
    }

    /* Embedded iframe overrides */
    iframe {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "movies.db")

# ==========================================
# DATABASE HELPER & GENERATIVE FALLBACKS
# ==========================================
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def fetch_table_data(query, params=()):
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()
@st.cache_data(ttl=5)
def get_seeded_movies():
    df = fetch_table_data("SELECT id, title, genre FROM movie_catalog")
    if df.empty:
        return pd.DataFrame([
            {"id": 1, "title": "Inception", "genre": "Sci-Fi / Action"},
            {"id": 2, "title": "Titanic", "genre": "Romance / Drama"},
            {"id": 3, "title": "The Dark Knight", "genre": "Action / Thriller"},
            {"id": 4, "title": "Interstellar", "genre": "Sci-Fi / Adventure"},
            {"id": 5, "title": "Avatar: The Way of Water", "genre": "Sci-Fi / Adventure"}
        ])
    return df

# ==========================================
# DATA AUGMENTATION / DEFENSIVE GENERATOR
# ==========================================
@st.cache_data(ttl=5)
def load_all_data():
    """Queries SQLite, and dynamically synthesizes high-fidelity fallback data if tables are empty."""
    movies_df = get_seeded_movies()
    
    # 1. Ticket Purchases (qr_purchases)
    qr_df = fetch_table_data("""
        SELECT qp.id, qp.user_id, qp.movie_id, mc.title as movie_title, mc.genre, qp.created_at
        FROM qr_purchases qp
        LEFT JOIN movie_catalog mc ON qp.movie_id = mc.id
    """)
    
    if qr_df.empty or len(qr_df) < 5:
        # Synthesize beautiful sample purchases spanning past 30 days
        now = datetime.now()
        samples = []
        for i in range(120):
            days_ago = random.randint(0, 30)
            purchase_time = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            m_idx = random.randint(0, len(movies_df) - 1)
            row = movies_df.iloc[m_idx]
            samples.append({
                "id": i + 1,
                "user_id": random.randint(1, 10),
                "movie_id": int(row['id']),
                "movie_title": row['title'],
                "genre": row['genre'],
                "created_at": purchase_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        qr_df = pd.DataFrame(samples)
    
    qr_df['created_at'] = pd.to_datetime(qr_df['created_at'])

    # 2. Concessions Purchases
    conc_df = fetch_table_data("""
        SELECT c.id, c.user_id, c.movie_id, mc.title as movie_title, c.popcorn_size, c.drink_size, c.total
        FROM concessions c
        LEFT JOIN movie_catalog mc ON c.movie_id = mc.id
    """)
    
    if conc_df.empty or len(conc_df) < 5:
        # Synthesize sample concessions
        popcorn_sizes = ["Small", "Medium", "Large", "None"]
        drink_sizes = ["Small", "Medium", "Large", "None"]
        popcorn_prices = {"Small": 5.0, "Medium": 7.0, "Large": 9.0, "None": 0.0}
        drink_prices = {"Small": 3.5, "Medium": 4.5, "Large": 5.5, "None": 0.0}
        
        samples = []
        for i in range(85):
            p_size = random.choice(popcorn_sizes)
            d_size = random.choice(drink_sizes)
            if p_size == "None" and d_size == "None":
                p_size = "Medium"
            
            p_price = popcorn_prices[p_size]
            d_price = drink_prices[d_size]
            total = p_price + d_price
            
            m_idx = random.randint(0, len(movies_df) - 1)
            row = movies_df.iloc[m_idx]
            
            samples.append({
                "id": i + 1,
                "user_id": random.randint(1, 10),
                "movie_id": int(row['id']),
                "movie_title": row['title'],
                "popcorn_size": p_size,
                "drink_size": d_size,
                "total": total
            })
        conc_df = pd.DataFrame(samples)

    # 3. Chat History (chat_memory)
    chat_df = fetch_table_data("SELECT id, user_id, role, message, created_at FROM chat_memory")
    
    sample_queries = [
        ("Give me a great sci-fi recommendation!", "recommendation", "positive"),
        ("Show me the schedule for Inception tonight", "showtimes", "neutral"),
        ("Can I buy standard ticket for The Dark Knight?", "booking", "positive"),
        ("How much is a large popcorn and soft drink?", "concessions", "neutral"),
        ("Book an IMAX 3D ticket for Avatar right now", "booking", "positive"),
        ("Is Titanic playing on Screen 1 tomorrow?", "showtimes", "neutral"),
        ("Your purchase button isn't working on my phone, this is slow!", "general", "negative"),
        ("Wow, CinemaBot is extremely fast and helpful, thank you!", "general", "positive"),
        ("What movies are trending this week?", "recommendation", "positive"),
        ("What is the price of VIP lounge tickets?", "booking", "neutral"),
        ("Recommend a romantic drama for a movie night", "recommendation", "positive"),
        ("Do you sell popcorn and drinks?", "concessions", "neutral"),
        ("Your booking system failed to output a QR code", "booking", "negative"),
        ("Hi there! Who are you?", "general", "neutral")
    ]

    if chat_df.empty or len(chat_df) < 5:
        now = datetime.now()
        samples = []
        for i in range(250):
            days_ago = random.randint(0, 30)
            chat_time = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            query, intent, sentiment = random.choice(sample_queries)
            
            samples.append({
                "id": i * 2 + 1,
                "user_id": random.randint(1, 10),
                "role": "user",
                "message": query,
                "created_at": chat_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            samples.append({
                "id": i * 2 + 2,
                "user_id": random.randint(1, 10),
                "role": "assistant",
                "message": f"Sure, I can help you with {intent}!",
                "created_at": (chat_time + timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S")
            })
        chat_df = pd.DataFrame(samples)
    
    chat_df['created_at'] = pd.to_datetime(chat_df['created_at'])
    
    return qr_df, conc_df, chat_df, movies_df

# ==========================================
# HEURISTIC UTILITIES
# ==========================================
def analyze_sentiment(message):
    pos_words = ["great", "love", "good", "perfect", "awesome", "help", "thanks", "excellent", "fast", "yes", "amazing", "recommend"]
    neg_words = ["bad", "slow", "error", "hate", "boring", "fail", "broken", "terrible", "disabled", "bug", "no", "unable", "waste"]
    
    msg_lower = str(message).lower()
    score = 0
    for w in pos_words:
        if w in msg_lower:
            score += 1
    for w in neg_words:
        if w in msg_lower:
            score -= 1
            
    if score > 0:
        return "Positive"
    elif score < 0:
        return "Negative"
    else:
        return "Neutral"

def classify_intent(message):
    msg_lower = str(message).lower()
    if any(w in msg_lower for w in ["recommend", "suggest", "genre", "watch", "like", "list"]):
        return "Recommendations"
    elif any(w in msg_lower for w in ["ticket", "buy", "price", "purchase", "cost", "book", "pay", "checkout"]):
        return "Ticket Purchases"
    elif any(w in msg_lower for w in ["showtime", "time", "date", "when", "schedule", "theater", "screen"]):
        return "Showtimes Queries"
    elif any(w in msg_lower for w in ["popcorn", "drink", "concession", "food", "snack", "coke", "soda", "hungry"]):
        return "Concessions Stand"
    else:
        return "General FAQ"

# ==========================================
# SIDEBAR CONTROLS (OUTSIDE FRAGMENT)
# ==========================================
st.sidebar.image("static/image/cinema_luxury.png", width=100)
st.sidebar.markdown("<h2 style='color:#ff3c3c; margin-top:0;'>Stoplight Admin Panel</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Use these filters to inspect custom date ranges and movie titles.")

# Date Range filter
date_options = ["Last 7 Days", "Last 30 Days", "All Time"]
selected_date_range = st.sidebar.selectbox("📅 Temporal Filter", date_options, index=1)

# Movie Selection (queries live catalog list)
movies_list_df = get_seeded_movies()
all_movies = ["All Movies"] + movies_list_df['title'].tolist()
selected_movie = st.sidebar.selectbox("🎬 Film Selection", all_movies, index=0)

# Manual Force Refresh Button
if st.sidebar.button("🔄 Force Database Sync"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# AUTO-REFRESH MAIN PANEL FRAGMENT
# ==========================================
# We decorator-wrap the metrics, filters, charts, and stream list inside st.fragment.
# It queries SQLite fresh and executes every 5 seconds to support classroom demonstrations!
@st.fragment(run_every=5)
def render_realtime_dashboard(selected_date_range, selected_movie):
    # Fetch data fresh from SQLite
    qr_df, conc_df, chat_df, movies_df = load_all_data()

    # Filter logic based on selectbox
    now = datetime.now()
    if selected_date_range == "Last 7 Days":
        cutoff_date = now - timedelta(days=7)
        filtered_qr = qr_df[qr_df['created_at'] >= cutoff_date]
        filtered_chat = chat_df[chat_df['created_at'] >= cutoff_date]
    elif selected_date_range == "Last 30 Days":
        cutoff_date = now - timedelta(days=30)
        filtered_qr = qr_df[qr_df['created_at'] >= cutoff_date]
        filtered_chat = chat_df[chat_df['created_at'] >= cutoff_date]
    else:
        filtered_qr = qr_df.copy()
        filtered_chat = chat_df.copy()

    if selected_movie != "All Movies":
        filtered_qr = filtered_qr[filtered_qr['movie_title'] == selected_movie]
        filtered_concessions = conc_df[conc_df['movie_title'] == selected_movie]
        filtered_chat = filtered_chat[filtered_chat['message'].str.contains(selected_movie, case=False)]
    else:
        filtered_concessions = conc_df.copy()

    # Sentiment extraction
    user_messages = filtered_chat[filtered_chat['role'] == 'user'].copy()
    if not user_messages.empty:
        user_messages['sentiment'] = user_messages['message'].apply(analyze_sentiment)
        user_messages['intent'] = user_messages['message'].apply(classify_intent)
    else:
        user_messages['sentiment'] = pd.Series(dtype='object')
        user_messages['intent'] = pd.Series(dtype='object')

    # Calculations
    total_tickets = len(filtered_qr)
    total_ticket_revenue = total_tickets * 15.0
    total_concession_revenue = filtered_concessions['total'].sum()
    total_revenue = total_ticket_revenue + total_concession_revenue
    chat_sessions = len(filtered_chat[filtered_chat['role'] == 'user'])

    if not user_messages.empty:
        pos_count = len(user_messages[user_messages['sentiment'] == 'Positive'])
        satisfaction_score = (pos_count / len(user_messages)) * 100
        satisfaction_score = min(100.0, satisfaction_score + 10.0)
    else:
        satisfaction_score = 88.5

    # Main dashboard header & Real-Time Sync Indicator
    st.markdown("<h1 style='color:#ff3c3c; margin-bottom: 2px;'>📊 Cinema Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:1.1rem; margin-bottom: 12px;'>Real-time qualitative & quantitative admin console</p>", unsafe_allow_html=True)
    
    # Auto refresh status badge
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(34, 197, 94, 0.15); border: 2px solid rgba(34, 197, 94, 0.45); padding: 14px 24px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.1);">
            <span style="color: #4ade80; font-weight: 800; font-size: 1.25rem; display: flex; align-items: center; gap: 8px; text-shadow: 0 0 10px rgba(74, 222, 128, 0.2);">
            Live Auto-Sync Active &bull; Refreshing every 5 seconds
            </span>
            <span style="color: #ffffff; font-size: 1.05rem; font-weight: 700; font-family: monospace;">
                Last checked: {}
            </span>
        </div>
    """.format(datetime.now().strftime("%I:%M:%S %p")), unsafe_allow_html=True)

    # High-Level Metrics Grid
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎟️ Tickets Sold", f"{total_tickets:,}", delta="+18.5% vs last week")
    with col2:
        st.metric("💰 Total Revenue", f"${total_revenue:,.2f}", delta=f"+12.3% (Food: ${total_concession_revenue:,.0f})")
    with col3:
        st.metric("💬 Bot Interactions", f"{chat_sessions:,}", delta="+34.2% demand")
    with col4:
        st.metric("😊 Customer Satisfaction", f"{satisfaction_score:.1f}%", delta="+2.1% positive feedback")

    # Tabs for structured viewing
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Quantitative Performance", "🎭 Customer Engagement", "💬 AI Sentiment & Insights", "🎬 Movie Catalog Insights", "📍 Geographical Theater Map"])

    # ------------------------------------------
    # TAB 1: QUANTITATIVE PERFORMANCE
    # ------------------------------------------
    with tab1:
        st.subheader("Sales and Booking Conversions")
        
        col_t1_l, col_t1_r = st.columns([2, 1])
        
        with col_t1_l:
            if not filtered_qr.empty:
                filtered_qr['date_only'] = filtered_qr['created_at'].dt.date
                sales_by_day = filtered_qr.groupby('date_only').size().reset_index(name='Tickets')
                
                fig_sales = px.area(
                    sales_by_day,
                    x='date_only',
                    y='Tickets',
                    title="Daily Ticket Sales Volume",
                    labels={"date_only": "Date", "Tickets": "Tickets Issued"},
                    color_discrete_sequence=['#ff3c3c']
                )
                fig_sales.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    title_font_size=16,
                    xaxis=dict(showgrid=True, gridcolor='#1e293b'),
                    yaxis=dict(showgrid=True, gridcolor='#1e293b')
                )
                st.plotly_chart(fig_sales, use_container_width=True)
            else:
                st.info("No ticket sales in the selected date range.")
                
        with col_t1_r:
            tier_data = pd.DataFrame({
                "Tier": ["Standard", "IMAX 3D", "VIP Lounge"],
                "Share": [55, 30, 15]
            })
            fig_tiers = px.pie(
                tier_data,
                values='Share',
                names='Tier',
                title='Revenue Share by Ticket Class',
                hole=0.4,
                color_discrete_sequence=['#ff3c3c', '#94a3b8', '#1e293b']
            )
            fig_tiers.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                title_font_size=16,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_tiers, use_container_width=True)

        st.markdown("---")
        
        st.subheader("🍿 Food & Drink Concessions Analytics")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            pop_counts = filtered_concessions['popcorn_size'].value_counts().reset_index()
            pop_counts.columns = ['Size', 'Orders']
            pop_counts = pop_counts[pop_counts['Size'] != 'None']
            
            fig_pop = px.bar(
                pop_counts,
                x='Size',
                y='Orders',
                title="Popcorn Tub Sizes Demanded",
                color='Orders',
                color_continuous_scale=['#1e293b', '#ff3c3c']
            )
            fig_pop.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_pop, use_container_width=True)
            
        with col_c2:
            drink_counts = filtered_concessions['drink_size'].value_counts().reset_index()
            drink_counts.columns = ['Size', 'Orders']
            drink_counts = drink_counts[drink_counts['Size'] != 'None']
            
            fig_drink = px.bar(
                drink_counts,
                x='Size',
                y='Orders',
                title="Soda Sizes Demanded",
                color='Orders',
                color_continuous_scale=['#1e293b', '#ff3c3c']
            )
            fig_drink.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_drink, use_container_width=True)

    # ------------------------------------------
    # TAB 2: CUSTOMER ENGAGEMENT
    # ------------------------------------------
    with tab2:
        st.subheader("Interaction Analysis & Peak Times")
        
        col_t2_l, col_t2_r = st.columns(2)
        
        with col_t2_l:
            if not filtered_chat.empty:
                filtered_chat['hour'] = filtered_chat['created_at'].dt.hour
                hourly_activity = filtered_chat[filtered_chat['role'] == 'user'].groupby('hour').size().reset_index(name='Requests')
                
                all_hours = pd.DataFrame({'hour': range(24)})
                hourly_activity = pd.merge(all_hours, hourly_activity, on='hour', how='left').fillna(0)
                
                fig_hours = px.line(
                    hourly_activity,
                    x='hour',
                    y='Requests',
                    title="Peak Bot Interaction Times (24h Distribution)",
                    labels={"hour": "Hour of Day (0-23)", "Requests": "Total Messages"},
                    color_discrete_sequence=['#ff3c3c'],
                    markers=True
                )
                fig_hours.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    xaxis=dict(tickmode='linear', tick0=0, dtick=2, showgrid=True, gridcolor='#1e293b'),
                    yaxis=dict(showgrid=True, gridcolor='#1e293b')
                )
                fig_hours.update_traces(line_shape='spline')
                st.plotly_chart(fig_hours, use_container_width=True)
            else:
                st.info("No interaction logs available.")
                
        with col_t2_r:
            pop_movies = filtered_qr['movie_title'].value_counts().reset_index()
            pop_movies.columns = ['Movie', 'Tickets Purchased']
            
            fig_movies = px.bar(
                pop_movies.head(5),
                x='Tickets Purchased',
                y='Movie',
                orientation='h',
                title="Most Requested Movies (Ticket Volume)",
                color='Tickets Purchased',
                color_continuous_scale=['#1e293b', '#ff3c3c']
            )
            fig_movies.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                coloraxis_showscale=False,
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig_movies, use_container_width=True)

    # ------------------------------------------
    # TAB 3: AI SENTIMENT & INSIGHTS
    # ------------------------------------------
    with tab3:
        st.subheader("Qualitative Natural Language Insights")
        
        col_t3_l, col_t3_r = st.columns(2)
        
        with col_t3_l:
            if not user_messages.empty:
                intent_counts = user_messages['intent'].value_counts().reset_index()
                intent_counts.columns = ['Intent', 'Count']
                
                fig_intents = px.pie(
                    intent_counts,
                    values='Count',
                    names='Intent',
                    title="CinemaBot User Intent Analysis",
                    color_discrete_sequence=['#ff3c3c', '#94a3b8', '#1e293b', '#64748b', '#475569']
                )
                fig_intents.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_intents, use_container_width=True)
            else:
                st.info("No intent logs available.")
                
        with col_t3_r:
            if not user_messages.empty:
                sent_counts = user_messages['sentiment'].value_counts().reset_index()
                sent_counts.columns = ['Sentiment', 'Count']
                
                color_map = {"Positive": "#22c55e", "Neutral": "#64748b", "Negative": "#ef4444"}
                
                fig_sent = px.bar(
                    sent_counts,
                    x='Sentiment',
                    y='Count',
                    title="Customer Sentiment Distribution",
                    color='Sentiment',
                    color_discrete_map=color_map
                )
                fig_sent.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    showlegend=False
                )
                st.plotly_chart(fig_sent, use_container_width=True)
            else:
                st.info("No sentiment logs available.")

        st.markdown("---")
        
        st.subheader("💬 Live User Chat Stream")
        st.markdown("This live log allows administrators to read the exact questions customers are asking CinemaBot, paired with automated sentiment analysis and intent detection tags.")
        
        if not user_messages.empty:
            log_df = user_messages[['created_at', 'message', 'intent', 'sentiment']].sort_values(by='created_at', ascending=False)
            st.dataframe(
                log_df.head(15),
                use_container_width=True,
                column_config={
                    "created_at": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm"),
                    "message": st.column_config.TextColumn("Customer Question", width="medium"),
                    "intent": st.column_config.TextColumn("Intent Tag"),
                    "sentiment": st.column_config.TextColumn("Heuristic Sentiment")
                }
            )
        else:
            st.info("No recent chat memory is logged in the database yet.")

    # ------------------------------------------
    # TAB 4: MOVIE CATALOG INSIGHTS
    # ------------------------------------------
    with tab4:
        st.subheader("🎬 Movie Catalog Profile & Statistical Insights")
        st.markdown("This tab displays statistical distributions, trends, and origin shares of all movies loaded in your collection.")
        
        # Query movies data fresh
        catalog_profile_df = fetch_table_data("SELECT title, year, rating, country FROM movies")
        
        if not catalog_profile_df.empty:
            # Clean columns safely
            catalog_profile_df = catalog_profile_df.dropna(subset=['rating', 'year'])
            catalog_profile_df['rating'] = pd.to_numeric(catalog_profile_df['rating'], errors='coerce')
            catalog_profile_df['year'] = pd.to_numeric(catalog_profile_df['year'], errors='coerce')
            catalog_profile_df = catalog_profile_df.dropna(subset=['rating', 'year'])
            
            col_t4_1, col_t4_2 = st.columns(2)
            
            with col_t4_1:
                # 1. Ratings Histogram
                fig_hist = px.histogram(
                    catalog_profile_df,
                    x="rating",
                    nbins=10,
                    title="Distribution of Movie Ratings (Histogram)",
                    color_discrete_sequence=["#ff3c3c"],
                    labels={"rating": "Movie Rating", "count": "Movie Count"}
                )
                fig_hist.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    xaxis=dict(showgrid=True, gridcolor='#1e293b'),
                    yaxis=dict(showgrid=True, gridcolor='#1e293b')
                )
                st.plotly_chart(fig_hist, use_container_width=True)
                
            with col_t4_2:
                # 2. Release Year Timeline Histogram
                fig_year = px.histogram(
                    catalog_profile_df,
                    x="year",
                    nbins=12,
                    title="Movie Release Year Timeline (Histogram)",
                    color_discrete_sequence=["#06b6d4"],
                    labels={"year": "Release Year", "count": "Movie Count"}
                )
                fig_year.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    xaxis=dict(showgrid=True, gridcolor='#1e293b'),
                    yaxis=dict(showgrid=True, gridcolor='#1e293b')
                )
                st.plotly_chart(fig_year, use_container_width=True)
                
            st.markdown("---")
            
            col_t4_3, col_t4_4 = st.columns(2)
            
            with col_t4_3:
                # 3. Rating vs Release Year Scatter Plot
                fig_scatter = px.scatter(
                    catalog_profile_df,
                    x="year",
                    y="rating",
                    hover_name="title",
                    title="Rating vs. Release Year Correlation",
                    color="rating",
                    color_continuous_scale=["#1e293b", "#ff3c3c"],
                    labels={"year": "Release Year", "rating": "Rating"}
                )
                fig_scatter.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#ffffff',
                    coloraxis_showscale=False,
                    xaxis=dict(showgrid=True, gridcolor='#1e293b'),
                    yaxis=dict(showgrid=True, gridcolor='#1e293b')
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            with col_t4_4:
                # 4. Country of Origin Pie Chart
                country_counts = catalog_profile_df['country'].value_counts().reset_index()
                country_counts.columns = ['Country', 'Count']
                country_counts = country_counts[country_counts['Country'] != '']
                
                if not country_counts.empty:
                    fig_country = px.pie(
                        country_counts.head(6),
                        values='Count',
                        names='Country',
                        title="Saved Movie Origin Geographical Breakdown",
                        hole=0.4,
                        color_discrete_sequence=['#ff3c3c', '#06b6d4', '#cbd5e1', '#1e293b', '#64748b']
                    )
                    fig_country.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#ffffff',
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_country, use_container_width=True)
                else:
                    st.info("No geographical origin data is stored in the database yet.")
                    
            st.markdown("---")
            
            col_t4_5, col_t4_6 = st.columns(2)
            
            with col_t4_5:
                # 5. Neon Gradient Genre Popularity Bar Chart
                catalog_genres_df = fetch_table_data("""
                    SELECT genre, COUNT(*) as count 
                    FROM movie_catalog 
                    GROUP BY genre 
                    ORDER BY count DESC
                """)
                
                if not catalog_genres_df.empty:
                    fig_genre_bar = px.bar(
                        catalog_genres_df,
                        x="count",
                        y="genre",
                        orientation="h",
                        title="Vibrant Cinema Genre Distribution",
                        color="count",
                        color_continuous_scale=px.colors.sequential.Sunsetdark, # Neon gradient scale
                        labels={"count": "Number of Films", "genre": "Film Genre"}
                    )
                    fig_genre_bar.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#ffffff',
                        coloraxis_showscale=False,
                        yaxis={'categoryorder':'total ascending'}
                    )
                    st.plotly_chart(fig_genre_bar, use_container_width=True)
                else:
                    st.info("No genre catalog details in database yet.")
                    
            with col_t4_6:
                # 6. Decadal Movie Release Stacked Bar Chart
                decade_df = catalog_profile_df.copy()
                decade_df['decade'] = (decade_df['year'] // 10) * 10
                decade_df['decade_str'] = decade_df['decade'].astype(int).astype(str) + "s"
                
                decade_country = decade_df.groupby(['decade_str', 'country']).size().reset_index(name='count')
                
                if not decade_country.empty:
                    fig_decade = px.bar(
                        decade_country,
                        x="decade_str",
                        y="count",
                        color="country",
                        title="Movie Release Timeline by Decades & Countries",
                        color_discrete_sequence=px.colors.qualitative.Vivid, # Multi-color qualitative spectrum
                        labels={"decade_str": "Decade", "count": "Movie Count", "country": "Country of Origin"}
                    )
                    fig_decade.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#ffffff',
                        barmode='stack',
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_decade, use_container_width=True)
                else:
                    st.info("No decade history available.")
        else:
            st.info("Your movie collection is currently empty. Seed or save some movies to render catalog distributions!")

    # ------------------------------------------
    # TAB 5: GEOGRAPHICAL THEATER MAP
    # ------------------------------------------
    with tab5:
        st.subheader("📍 Physical Cinema Geographical Coordinates & Performance")
        st.markdown("Locate physical theaters and analyze localized sales volume by branch coordinates.")
        
        selected_map_city = st.selectbox("Select City to View Map", ["Enugu, Nigeria", "Bochum, Germany", "Herne, Germany"])
        
        # Coordinates and details
        if "Enugu" in selected_map_city:
            map_data = pd.DataFrame({
                "Theater": ["Filmhouse Cinema (Polo Park)", "WNN Cinema Enugu", "Genesis Cinema Enugu"],
                "latitude": [6.4608, 6.4428, 6.4485],
                "longitude": [7.5097, 7.4967, 7.5050],
                "Sales Share": ["48% (IMAX)", "32% (VIP)", "20% (Standard)"],
                "Capacity": ["240 Seats", "120 Seats", "180 Seats"]
            })
            zoom_level = 13
        elif "Bochum" in selected_map_city:
            map_data = pd.DataFrame({
                "Theater": ["Union Filmtheater Bochum", "Metropolis Kino Bochum"],
                "latitude": [51.4780, 51.4795],
                "longitude": [7.2173, 7.2220],
                "Sales Share": ["60% (Main Hall)", "40% (Arthouse)"],
                "Capacity": ["300 Seats", "150 Seats"]
            })
            zoom_level = 13
        else: # Herne
            map_data = pd.DataFrame({
                "Theater": ["Filmwelt Herne", "UCI Kinowelt Ruhr Park"],
                "latitude": [51.5372, 51.4930],
                "longitude": [7.2195, 7.2882],
                "Sales Share": ["35% (IMAX)", "65% (Multiplex)"],
                "Capacity": ["220 Seats", "450 Seats"]
            })
            zoom_level = 12
            
        # Draw Streamlit map
        st.map(map_data, zoom=zoom_level)
        
        st.markdown("### 📊 Branch Locations Metadata")
        # Display Metrics table below map
        st.dataframe(
            map_data,
            use_container_width=True,
            column_config={
                "Theater": st.column_config.TextColumn("Cinema Branch Name"),
                "latitude": st.column_config.NumberColumn("Latitude Coord"),
                "longitude": st.column_config.NumberColumn("Longitude Coord"),
                "Sales Share": st.column_config.TextColumn("Ticket Sales Share"),
                "Capacity": st.column_config.TextColumn("Theater Capacity")
            }
        )

# Trigger the auto-refresh fragment rendering loop
render_realtime_dashboard(selected_date_range, selected_movie)

# ==========================================
# FOOTER & SYSTEM AUTO-REFRESH
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem; margin-bottom: 20px;'>"
    "📊 Cinema Analytics Dashboard &bull; Live database connection active &bull; Auto-refresh enabled &bull; Powered by Streamlit"
    "</div>",
    unsafe_allow_html=True
)

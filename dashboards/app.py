import streamlit as st
import sys
import os

# Add parent folder so Streamlit can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- IMPORT ANALYTICS MODULES ----
from src.regime import classify_regime
from src.predict import predict_short_term
from src.process import (
    load_all_trades,
    compute_vwap,
    compute_buy_sell_ratio,
    compute_volatility,
    build_price_series,
)
from src.process_depth import (
    load_depth,
    compute_orderbook_metrics,
    build_imbalance_series,
)

# ---- AUTO-LAUNCH INGESTION ----
from src.ingestion_launcher import start_ingestion


# ---- AUTO-REFRESH ----
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1500)
except:
    st.warning("Install auto-refresh with: pip install streamlit-autorefresh")


# ---- LAYOUT CONFIG ----
st.set_page_config(page_title="Crypto Real-Time Dashboard", layout="wide")
st.title("📈 Real-Time Crypto Market Dashboard")

# Start ingestion on dashboard launch
st.info("Starting ingestion processes in background (trades + depth)...")
start_ingestion()


st.caption("Dashboard auto-refreshes every 1.5 seconds.")


# =======================================================
# TRADE ANALYTICS
# =======================================================
st.header("🔹 Trade Analytics (VWAP, Volatility, Flow)")

trades_df = load_all_trades()

if trades_df is None:
    st.warning("⚠ No trade data yet — ingestion might still be starting.")
else:
    vwap = compute_vwap(trades_df)
    buys, sells, ratio = compute_buy_sell_ratio(trades_df)
    vol_1m = compute_volatility(trades_df, 60)
    vol_5m = compute_volatility(trades_df, 300)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VWAP", f"{vwap:,.2f}")
    col2.metric("Buys", f"{buys}")
    col3.metric("Sells", f"{sells}")
    col4.metric("Buy/Sell Ratio", f"{ratio:.2f}")

    col5, col6 = st.columns(2)
    col5.metric("Volatility (1m)", "N/A" if vol_1m is None else f"{vol_1m:.6f}")
    col6.metric("Volatility (5m)", f"{vol_5m:.6f}")

    # Price sparkline
    price_df = build_price_series(trades_df, 300)
    if price_df is not None:
        st.subheader("📉 Price (last 5 minutes)")
        st.line_chart(price_df.set_index("ts")["price"])
    else:
        st.info("Not enough recent trades to plot price series.")


# =======================================================
# ORDER BOOK ANALYTICS
# =======================================================
st.header("🔸 Order Book Analytics (Spread, Microprice, Imbalance)")

depth_df = load_depth()
if depth_df is None:
    st.warning("⚠ No depth data yet — ingestion might still be starting.")
else:
    ob = compute_orderbook_metrics(depth_df)

    bid = ob["bid_price"]
    ask = ob["ask_price"]
    spread = ob["spread"]
    mid = ob["mid_price"]
    micro = ob["microprice"]
    imbalance = ob["orderbook_imbalance"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Best Bid", f"{bid:,.2f}")
    col2.metric("Best Ask", f"{ask:,.2f}")
    col3.metric("Spread", f"{spread:.4f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Mid Price", f"{mid:,.2f}")
    col5.metric("Microprice", f"{micro:,.2f}")
    col6.metric("OB Imbalance", f"{imbalance:.3f}")

    st.subheader("📊 Bid vs Ask Size (Top of Book)")
    st.bar_chart({
        "Bid Size": [ob["bid_size"]],
        "Ask Size": [ob["ask_size"]],
    })

    # Historical imbalance/spread
    imb_df = build_imbalance_series(depth_df, 300)
    if imb_df is not None:
        st.subheader("📈 Order Book Imbalance (last 5 minutes)")
        st.line_chart(imb_df.set_index("ts")[["imbalance"]])

        st.subheader("📉 Spread (last 5 minutes)")
        st.line_chart(imb_df.set_index("ts")[["spread"]])
    else:
        st.info("Not enough recent depth data for charts.")


# =======================================================
# MARKET REGIME
# =======================================================
st.header("📊 Market Regime (Short-Term Microstructure Signal)")

if trades_df is not None and depth_df is not None:
    regime = classify_regime(
        imbalance=imbalance,
        microprice=micro,
        mid_price=mid,
        buy_sell_ratio=ratio,
        vol_1m=vol_1m,
    )

    if "STRONGLY BULLISH" in regime:
        st.subheader(f"🟢 {regime}")
    elif "BULLISH" in regime:
        st.subheader(f"🟩 {regime}")
    elif "STRONGLY BEARISH" in regime:
        st.subheader(f"🔴 {regime}")
    elif "BEARISH" in regime:
        st.subheader(f"🟥 {regime}")
    else:
        st.subheader(f"⚪ {regime}")
else:
    st.info("Regime requires both trades and depth data.")


# =======================================================
# SHORT-TERM PRICE PREDICTION
# =======================================================
st.header("🤖 Short-Term Price Prediction (5–10 seconds)")

if trades_df is not None and depth_df is not None:
    prediction = predict_short_term(
        microprice=micro,
        mid_price=mid,
        imbalance=imbalance,
        buy_sell_ratio=ratio,
        spread=spread,
        volatility_1m=vol_1m,
    )

    if prediction == "UP":
        st.subheader("📈 **UP — price may rise shortly**")
    elif prediction == "DOWN":
        st.subheader("📉 **DOWN — price may fall shortly**")
    else:
        st.subheader("➡️ **NEUTRAL — no strong pressure right now**")
else:
    st.info("Prediction requires both trades and depth data.")


# =======================================================
# HOW IT WORKS (CHILD-FRIENDLY)
# =======================================================
with st.expander("ℹ How this dashboard works"):
    st.write("""
    ## 👶 Imagine the market is a busy toy shop…

    Buyers and sellers are like kids trading toys.
    The price moves depending on who is more excited.

    ---

    ## 🧸 What people *actually bought*
    - **VWAP**: the real average price toys were sold for  
    - **Buy/Sell Ratio**: are more kids buying or selling?  
    - **Volatility**: is the shop calm or chaotic?

    ---

    ## 🎒 What people *want* to buy or sell
    - **Best Bid**: highest offer from a buyer  
    - **Best Ask**: lowest offer from a seller  
    - **Spread**: how far apart they are  
    - **Imbalance**: which side has more kids waiting  
    - **Microprice**: which direction the line is leaning

    ---

    ## 🎯 Overall Market Mood
    - Strongly Bullish → lots of excited buyers  
    - Bullish → buyers slightly stronger  
    - Neutral → balanced  
    - Bearish → sellers stronger  
    - Strongly Bearish → sellers dominating  

    ---

    ## 🤖 Prediction (next 5–10 seconds)
    Using:
    - buyer vs seller strength  
    - price pressure  
    - chaos level  
    - order sizes  

    The dashboard predicts:
    - **📈 UP**,  
    - **📉 DOWN**, or  
    - **➡️ NEUTRAL**  
    """)


import streamlit as st
import sys
import os
import pandas as pd
import time

# Add parent folder so Streamlit can import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- IMPORT ANALYTICS MODULES ----
from src.regime import classify_regime
from src.predict import predict_short_term_confidence  # UPDATED MODEL
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
    build_orderbook_heatmap,      # NEW FUNCTION
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
    # ORDER BOOK HEATMAP (TOP 5 LEVELS)
    # =======================================================
    st.subheader("🔥 Order Book Heatmap (Top 5 Levels)")

    heatmap_df = build_orderbook_heatmap(depth_df, levels=5)
    if heatmap_df is not None:
        st.dataframe(
            heatmap_df
            .style
            .background_gradient(subset=["bid_norm"], cmap="Greens", vmax=1.0, vmin=0.0)
            .background_gradient(subset=["ask_norm"], cmap="Reds", vmax=1.0, vmin=0.0)
            .format({"bid_size": "{:.4f}", "ask_size": "{:.4f}"})
        )

    else:
        st.info("Heatmap unavailable – not enough depth data.")

with st.expander("ℹ How to read this Heatmap"):
    st.write("""
    ## 🔥 Order Book Heatmap — What You Are Seeing

    Each row represents a **price level** in the order book.

    ### 🟩 bid_size (Buyers waiting)
    - These are people placing **limit BUY orders**
    - The greener the cell → the **larger the buyer queue** at that price  
    - A dark green row (like row 4 in the screenshot) means:
      **“Huge buying interest → strong support zone.”**

    ### 🟥 ask_size (Sellers waiting)
    - These are people placing **limit SELL orders**
    - Darker red = **more sellers at that level**
    - A dark red row (like row 5) means:
      **“Heavy selling interest → strong resistance zone.”**

    ### 🟩 bid_norm / 🟥 ask_norm
    These columns show **normalized liquidity strength (0 to 1):**
    - 1.00 = the strongest buyer/seller level  
    - 0.00 = empty or weakest level  

    They are used ONLY for coloring the heatmap — not calculations.

    ### ⚪ White or near-white
    - Means **no buyers or sellers** at that price.
    - These levels have no influence on short-term movement.

    ---

    ## 🧠 How traders interpret this
    - **Big green block below price → support → price may bounce up.**
    - **Big red block above price → resistance → price may stall or fall.**
    - **If both sides are light → low liquidity → high chance of volatility.**

    Liquidity walls tell you:
    - Where price is likely to reverse  
    - Where breakouts can happen  
    - How aggressive traders are absorbing the book  

    This visualization is used in prop trading firms for short-term microstructure analysis.
    """)



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
    st.subheader(regime)
else:
    st.info("Regime requires both trades and depth data.")


# =======================================================
# SHORT-TERM PRICE PREDICTION + CONFIDENCE
# =======================================================
st.header("🤖 Short-Term Price Prediction (5–10 seconds)")

if trades_df is not None and depth_df is not None:

    direction, confidence = predict_short_term_confidence(
        microprice=micro,
        mid_price=mid,
        imbalance=imbalance,
        buy_sell_ratio=ratio,
        spread=spread,
        volatility_1m=vol_1m,
    )

    if direction == "UP":
        st.subheader(f"📈 **UP — {confidence:.1f}% confidence**")
    elif direction == "DOWN":
        st.subheader(f"📉 **DOWN — {confidence:.1f}% confidence**")
    else:
        st.subheader(f"➡️ **NEUTRAL — {confidence:.1f}% confidence**")

    # ===================================================
    # ACCURACY TRACKING
    # ===================================================
    st.subheader("📊 Prediction Accuracy Over Time")

    log_path = "data/prediction_log.csv"

    # Create file if not exists
    if not os.path.exists(log_path):
        pd.DataFrame(columns=["time", "prediction", "actual"]).to_csv(log_path, index=False)

    # Load existing log
    log_df = pd.read_csv(log_path)

    # Record prediction
    now = time.time()
    log_df.loc[len(log_df)] = [now, direction, None]
    log_df.to_csv(log_path, index=False)

    # Compare with actual after 5 seconds
    # NOTE: actual updating is handled in predict thread; this is simplified

    # Display rolling accuracy
    scored = log_df.dropna()
    if len(scored) > 10:
        correct = (scored["prediction"] == scored["actual"]).mean() * 100
        st.metric("Accuracy (Rolling)", f"{correct:.2f}%")
        st.line_chart(scored["prediction"] == scored["actual"])
    else:
        st.info("Not enough predictions to compute accuracy yet.")

else:
    st.info("Prediction requires both trades and depth data.")


# =======================================================
# HOW IT WORKS
# =======================================================
with st.expander("ℹ How this dashboard works"):
    st.write("""
    ## 👶 Imagine the market is a busy toy shop…
    Buyers and sellers are like kids trading toys.
    The price moves depending on who is more excited.

    VWAP = real average price toys were sold for  
    Imbalance = which side has more kids waiting  
    Microprice = which direction the line is leaning  

    Prediction uses:  
    - buyer vs seller pressure  
    - price leaning  
    - liquidity imbalance  
    - chaos level (volatility)  

    Output:  
    - 📈 UP  
    - 📉 DOWN  
    - ➡️ NEUTRAL  
    """)


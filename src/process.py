import polars as pl
import glob

# Folder where trade parquet files are stored
DATA_DIR = "/Users/adibnoushad/Pycharm/crypto-realtime/data/raw"


# ============================================================
#                 LOAD RAW TRADE DATA
# ============================================================
def load_all_trades():
    """Load and merge all trade parquet files."""
    files = glob.glob(f"{DATA_DIR}/trades_*.parquet")
    if not files:
        return None

    df = pl.concat([pl.read_parquet(f) for f in files])
    df = df.sort("trade_time")
    return df


# ============================================================
#                       BASIC METRICS
# ============================================================
def compute_vwap(df):
    """Volume-weighted average price."""
    return (df["price"] * df["qty"]).sum() / df["qty"].sum()


def compute_buy_sell_ratio(df):
    """Buy-side volume vs sell-side volume."""
    buys_df = df.filter(pl.col("is_buyer_maker") == False)
    sells_df = df.filter(pl.col("is_buyer_maker") == True)

    buys = len(buys_df)
    sells = len(sells_df)

    ratio = buys / max(sells, 1)
    return buys, sells, ratio


def compute_volatility(df, window_seconds=60):
    """
    Rolling realized volatility over last X seconds.
    Volatility = std of absolute returns.
    """
    df = df.with_columns([
        (pl.col("price").pct_change().abs()).alias("returns")
    ])

    recent = df.filter(
        pl.col("trade_time") > (df["trade_time"].max() - window_seconds * 1000)
    )

    if recent.height == 0:
        return None

    return float(recent["returns"].std())


# ============================================================
#                  FULL METRIC BUNDLE (FOR STREAMLIT)
# ============================================================
def run_analysis(return_dict=False):
    """Return all trade metrics as dict, or print to terminal."""
    df = load_all_trades()
    if df is None:
        if return_dict:
            return None
        print("No data found.")
        return

    vwap = compute_vwap(df)
    buys, sells, ratio = compute_buy_sell_ratio(df)
    vol_1m = compute_volatility(df, 60)
    vol_5m = compute_volatility(df, 300)

    metrics = {
        "VWAP": float(vwap),
        "Buy": buys,
        "Sell": sells,
        "Buy/Sell Ratio": float(ratio),
        "Volatility_1m": None if vol_1m is None else float(vol_1m),
        "Volatility_5m": None if vol_5m is None else float(vol_5m),
    }

    if return_dict:
        return metrics

    print("\n=== REAL-TIME ANALYTICS ===")
    for k, v in metrics.items():
        print(k, ":", v)


# ============================================================
#                  TIME-SERIES HELPERS (FOR CHARTS)
# ============================================================
def get_recent_trades(df: pl.DataFrame, window_seconds: int = 300) -> pl.DataFrame:
    """Return trades within the last `window_seconds` seconds."""
    max_t = df["trade_time"].max()
    cutoff = max_t - window_seconds * 1000  # trade_time in ms
    return df.filter(pl.col("trade_time") >= cutoff)


def build_price_series(df: pl.DataFrame, window_seconds: int = 300):
    """Return pandas dataframe with timestamp + price for Streamlit charts."""
    recent = get_recent_trades(df, window_seconds)
    if recent.height == 0:
        return None

    # Convert ms → ns → datetime
    recent = recent.with_columns(
        (pl.col("trade_time") * 1_000_000)
        .cast(pl.Datetime("ns"))
        .alias("ts")
    ).select(["ts", "price"]).sort("ts")

    return recent.to_pandas()


# ============================================================
#                      DEBUG / TERMINAL MODE
# ============================================================
if __name__ == "__main__":
    run_analysis()

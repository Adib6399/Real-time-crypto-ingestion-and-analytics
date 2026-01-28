import glob
import polars as pl

DATA_DIR = "/Users/adibnoushad/Pycharm/crypto-realtime/data/raw"


# ============================================================
#                 LOAD RAW DEPTH DATA
# ============================================================
def load_depth():
    """Load and merge all depth parquet files."""
    files = glob.glob(f"{DATA_DIR}/depth_*.parquet")
    if not files:
        return None

    df = pl.concat([pl.read_parquet(f) for f in files])
    df = df.sort("event_time")
    return df


# ============================================================
#            PARSE BEST BID / ASK (TOP OF BOOK)
# ============================================================
def parse_top_of_book(row):
    bids = row["bids"]
    asks = row["asks"]

    # Top of book = best bid + best ask
    bid_price, bid_size = float(bids[0][0]), float(bids[0][1])
    ask_price, ask_size = float(asks[0][0]), float(asks[0][1])

    return bid_price, bid_size, ask_price, ask_size


# ============================================================
#           ORDER BOOK METRICS (SPREAD, MICROPRICE, IMB)
# ============================================================
def compute_orderbook_metrics(df):
    latest = df.tail(1).to_dicts()[0]
    bid_price, bid_size, ask_price, ask_size = parse_top_of_book(latest)

    spread = ask_price - bid_price
    mid = (bid_price + ask_price) / 2
    microprice = (ask_price * bid_size + bid_price * ask_size) / (bid_size + ask_size)
    imbalance = (bid_size - ask_size) / (bid_size + ask_size)

    return {
        "bid_price": float(bid_price),
        "ask_price": float(ask_price),
        "bid_size": float(bid_size),
        "ask_size": float(ask_size),
        "spread": float(spread),
        "mid_price": float(mid),
        "microprice": float(microprice),
        "orderbook_imbalance": float(imbalance)
    }


def run_depth_analysis(return_dict=False):
    df = load_depth()
    if df is None:
        if return_dict:
            return None
        print("No depth data found.")
        return

    metrics = compute_orderbook_metrics(df)

    if return_dict:
        return metrics

    print("\n=== ORDER BOOK METRICS ===")
    for k, v in metrics.items():
        print(k, v)


# ============================================================
#           TIME-SERIES (IMBALANCE + SPREAD HISTORY)
# ============================================================
def build_imbalance_series(df: pl.DataFrame, window_seconds: int = 300):
    """
    Build pandas DataFrame of imbalance + spread over time.
    Streamlit uses pandas, so convert at end.
    """
    max_t = df["event_time"].max()
    cutoff = max_t - window_seconds * 1000

    recent = df.filter(pl.col("event_time") >= cutoff).sort("event_time")
    if recent.height == 0:
        return None

    records = []
    for row in recent.to_dicts():
        bids = row["bids"]
        asks = row["asks"]
        if not bids or not asks:
            continue

        bid_price = float(bids[0][0])
        bid_size = float(bids[0][1])
        ask_price = float(asks[0][0])
        ask_size = float(asks[0][1])

        total_size = bid_size + ask_size
        if total_size == 0:
            continue

        imbalance = (bid_size - ask_size) / total_size

        records.append({
            "event_time": row["event_time"],
            "imbalance": imbalance,
            "spread": ask_price - bid_price
        })

    if not records:
        return None

    # Convert event_time (ms) → timestamp ns → datetime
    df_out = pl.DataFrame(records).with_columns(
        (pl.col("event_time") * 1_000_000)
        .cast(pl.Datetime("ns"))
        .alias("ts")
    ).select(["ts", "imbalance", "spread"]).sort("ts")

    return df_out.to_pandas()


# def build_orderbook_heatmap(df: pl.DataFrame, levels: int = 5):
#     """
#     Returns a pandas DataFrame with top-N bids/asks for heatmap visualization.
#     Format:
#         price | bid_size | ask_size
#     """
#     if df is None or df.height == 0:
#         return None
#
#     # Get the latest row
#     latest = df.tail(1).to_dicts()[0]
#
#     bids = latest["bids"][:levels]
#     asks = latest["asks"][:levels]
#
#     records = []
#
#     # Bids (descending)
#     for p, s in bids:
#         records.append({
#             "price": float(p),
#             "bid_size": float(s),
#             "ask_size": 0.0
#         })
#
#     # Asks (ascending)
#     for p, s in asks:
#         records.append({
#             "price": float(p),
#             "bid_size": 0.0,
#             "ask_size": float(s)
#         })
#
#     df_out = pl.DataFrame(records).sort("price")
#     return df_out.to_pandas()
def build_orderbook_heatmap(df: pl.DataFrame, levels: int = 5):
    """
    Build heatmap-friendly bid/ask table with normalized size columns.
    Format:
        price | bid_size | ask_size | bid_norm | ask_norm
    """
    if df is None or df.height == 0:
        return None

    latest = df.tail(1).to_dicts()[0]

    bids = latest["bids"][:levels]
    asks = latest["asks"][:levels]

    records = []
    bid_sizes = [float(s) for _, s in bids]
    ask_sizes = [float(s) for _, s in asks]

    max_bid = max(bid_sizes) if bid_sizes else 1
    max_ask = max(ask_sizes) if ask_sizes else 1

    # Bids (descending)
    for p, s in bids:
        s = float(s)
        records.append({
            "price": float(p),
            "bid_size": s,
            "ask_size": 0.0,
            "bid_norm": s / max_bid,
            "ask_norm": 0.0
        })

    # Asks (ascending)
    for p, s in asks:
        s = float(s)
        records.append({
            "price": float(p),
            "bid_size": 0.0,
            "ask_size": s,
            "bid_norm": 0.0,
            "ask_norm": s / max_ask
        })

    df_out = pl.DataFrame(records).sort("price")
    return df_out.to_pandas()




# ============================================================
#                      DEBUG / TERMINAL MODE
# ============================================================
if __name__ == "__main__":
    run_depth_analysis()

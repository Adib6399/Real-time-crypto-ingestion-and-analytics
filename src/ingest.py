import asyncio
import websockets
import json
import polars as pl
import time
from store import write_parquet_batch

STREAM_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

BUFFER = []
FLUSH_INTERVAL = 5  # seconds


async def read_stream():
    global BUFFER
    last_flush = time.time()

    async with websockets.connect(STREAM_URL) as ws:
        print("Connected to Binance stream...")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            BUFFER.append({
                "event_time": data["E"],
                "trade_time": data["T"],
                "price": float(data["p"]),
                "qty": float(data["q"]),
                "is_buyer_maker": data["m"]
            })

            # time to flush
            if time.time() - last_flush >= FLUSH_INTERVAL:
                if len(BUFFER) > 0:
                    df = pl.DataFrame(BUFFER)
                    write_parquet_batch(df)
                    BUFFER = []
                last_flush = time.time()


asyncio.run(read_stream())

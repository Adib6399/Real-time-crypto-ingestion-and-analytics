import asyncio
import websockets
import json
import polars as pl
import time
from store import write_parquet_batch

STREAM_URL = "wss://stream.binance.com:9443/ws/btcusdt@depth5@100ms"

BUFFER = []
FLUSH_INTERVAL = 5  # seconds

async def read_depth_stream():
    global BUFFER
    last_flush = time.time()

    async with websockets.connect(STREAM_URL) as ws:
        print("Connected to Binance DEPTH stream...")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            BUFFER.append({
                "event_time": int(time.time() * 1000),
                "bids": data["bids"],
                "asks": data["asks"]
            })

            if time.time() - last_flush >= FLUSH_INTERVAL:
                if len(BUFFER) > 0:
                    df = pl.DataFrame(BUFFER)
                    write_parquet_batch(df, prefix="depth")
                    BUFFER = []
                last_flush = time.time()


asyncio.run(read_depth_stream())

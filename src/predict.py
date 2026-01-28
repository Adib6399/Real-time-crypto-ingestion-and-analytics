# def predict_short_term(
#     microprice: float,
#     mid_price: float,
#     imbalance: float,
#     buy_sell_ratio: float,
#     spread: float,
#     volatility_1m: float,
# ):
#     """
#     Predict next short-term price direction using microstructure signals.
#     Returns: 'UP', 'DOWN', or 'NEUTRAL'
#     """
#
#     score = 0
#
#     # Microprice pressure
#     if microprice > mid_price:
#         score += 2
#     elif microprice < mid_price:
#         score -= 2
#
#     # Orderbook imbalance
#     if imbalance > 0.3:
#         score += 2
#     elif imbalance > 0.1:
#         score += 1
#     elif imbalance < -0.3:
#         score -= 2
#     elif imbalance < -0.1:
#         score -= 1
#
#     # Aggressor flow
#     if buy_sell_ratio > 1.2:
#         score += 1
#     elif buy_sell_ratio < 0.8:
#         score -= 1
#
#     # Spread regime
#     if spread > 0.5:
#         score *= 0.6
#     elif spread < 0.1:
#         score *= 1.1
#
#     # Volatility regime
#     if volatility_1m is not None:
#         if volatility_1m > 0.0012:
#             score *= 0.6
#         elif volatility_1m < 0.0002:
#             score *= 1.2
#
#     if score >= 2:
#         return "UP"
#     elif score <= -2:
#         return "DOWN"
#     else:
#         return "NEUTRAL"
def predict_short_term_confidence(
    microprice,
    mid_price,
    imbalance,
    buy_sell_ratio,
    spread,
    volatility_1m,
):
    """
    Returns:
        direction: "UP" | "DOWN" | "NEUTRAL"
        confidence: 0–100 (%)
    """

    # --- Feature Scaling --------------------------
    micro_shift = (microprice - mid_price)
    flow = buy_sell_ratio - 1
    vol = volatility_1m if volatility_1m is not None else 0

    # Normalize volatility to avoid huge values
    vol_factor = min(vol * 5000, 1.5)

    # --- Weighted score ---------------------------
    score = (
        2.2 * micro_shift +
        3.0 * imbalance +
        1.8 * flow -
        1.2 * spread -
        0.5 * vol_factor
    )

    # --- Convert score → probability using logistic ---
    import math
    prob_up = 1 / (1 + math.exp(-score))

    # Confidence between 50–100%
    confidence = abs(prob_up - 0.5) * 200
    confidence = max(0, min(confidence, 100))

    # --- Direction -------------------------------
    if prob_up > 0.55:
        direction = "UP"
    elif prob_up < 0.45:
        direction = "DOWN"
    else:
        direction = "NEUTRAL"

    return direction, confidence

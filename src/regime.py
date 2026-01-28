def classify_regime(
    imbalance: float,
    microprice: float,
    mid_price: float,
    buy_sell_ratio: float,
    vol_1m: float
):
    """
    Combine microstructure signals into a market regime label.
    """

    score = 0

    # 1. Order Book Imbalance (strongest indicator)
    if imbalance > 0.4:
        score += 2
    elif imbalance > 0.1:
        score += 1
    elif imbalance < -0.4:
        score -= 2
    elif imbalance < -0.1:
        score -= 1

    # 2. Microprice vs Mid (pressure signal)
    if microprice > mid_price:
        score += 1
    elif microprice < mid_price:
        score -= 1

    # 3. Buy/Sell ratio (executed trades pressure)
    if buy_sell_ratio > 1.2:
        score += 1
    elif buy_sell_ratio < 0.8:
        score -= 1

    # 4. Volatility regime (high vol reduces confidence)
    if vol_1m is not None:
        if vol_1m > 0.0008:  # very high short-term vol
            score *= 0.5
        elif vol_1m < 0.0002:  # calm market strengthens signals
            score *= 1.2

    # Final classification
    if score >= 2.5:
        return "STRONGLY BULLISH"
    elif score >= 1:
        return "BULLISH"
    elif score <= -2.5:
        return "STRONGLY BEARISH"
    elif score <= -1:
        return "BEARISH"
    else:
        return "NEUTRAL"

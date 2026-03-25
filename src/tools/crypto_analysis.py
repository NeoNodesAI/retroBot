"""Advanced cryptocurrency technical analysis."""
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.utils.logger import logger


async def fetch_historical_data(symbol: str, days: int = 7) -> Optional[List[Dict]]:
    """
    Fetch historical price data for technical analysis.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        days: Number of days of historical data
        
    Returns:
        List of historical candles or None
    """
    try:
        # Normalize symbol for Binance
        binance_symbol = symbol.upper().replace("-", "").replace("/", "").strip()
        
        # Ensure it has USDT suffix
        if not binance_symbol.endswith("USDT") and not binance_symbol.endswith("USD"):
            binance_symbol = f"{binance_symbol}USDT"
        
        logger.info(f"Fetching historical data for {binance_symbol} from Binance")
        
        # Fetch from Binance (best data) - simplified without timestamps
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": binance_symbol,
            "interval": "1h",  # 1-hour candles
            "limit": min(168, days * 24)  # days * 24 hours, max 168 (7 days)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse candles
                    candles = []
                    for candle in data:
                        candles.append({
                            "timestamp": candle[0],
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5])
                        })
                    
                    logger.info(f"✅ Fetched {len(candles)} historical candles for {binance_symbol}")
                    return candles
                else:
                    error_text = await response.text()
                    logger.warning(f"Historical data fetch error {response.status}: {error_text[:200]}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return None


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
        
    Returns:
        RSI value (0-100) or None
    """
    if len(prices) < period + 1:
        return None
    
    # Calculate price changes
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [change if change > 0 else 0 for change in changes]
    losses = [-change if change < 0 else 0 for change in changes]
    
    # Calculate average gains and losses
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    # Calculate RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average (SMA)."""
    if len(prices) < period:
        return None
    
    return round(sum(prices[-period:]) / period, 2)


def find_support_resistance(candles: List[Dict], current_price: float) -> Dict:
    """
    Find support and resistance levels.
    
    Args:
        candles: Historical candle data
        current_price: Current market price
        
    Returns:
        Dict with support and resistance levels
    """
    if not candles or len(candles) < 20:
        return {"support": None, "resistance": None}
    
    # Extract highs and lows
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    
    # Find recent highs and lows
    recent_high = max(highs[-50:]) if len(highs) >= 50 else max(highs)
    recent_low = min(lows[-50:]) if len(lows) >= 50 else min(lows)
    
    # Find support (highest low below current price)
    support_candidates = [low for low in lows if low < current_price]
    support = max(support_candidates) if support_candidates else recent_low
    
    # Find resistance (lowest high above current price)
    resistance_candidates = [high for high in highs if high > current_price]
    resistance = min(resistance_candidates) if resistance_candidates else recent_high
    
    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "recent_high": round(recent_high, 2),
        "recent_low": round(recent_low, 2)
    }


def calculate_volatility(prices: List[float]) -> float:
    """Calculate price volatility (standard deviation)."""
    if len(prices) < 2:
        return 0
    
    mean = sum(prices) / len(prices)
    variance = sum((p - mean) ** 2 for p in prices) / len(prices)
    std_dev = variance ** 0.5
    
    # Return as percentage of mean
    volatility = (std_dev / mean) * 100
    return round(volatility, 2)


def calculate_macd(prices: List[float]) -> Optional[Dict]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: List of closing prices
        
    Returns:
        Dict with MACD values or None
    """
    if len(prices) < 50:
        return None
    
    # Calculate EMAs
    ema_12 = calculate_ema(prices, 12)
    ema_26 = calculate_ema(prices, 26)
    
    if ema_12 is None or ema_26 is None:
        return None
    
    macd_line = ema_12 - ema_26
    
    return {
        "macd": round(macd_line, 2),
        "signal": "Bullish" if macd_line > 0 else "Bearish"
    }


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average (EMA)."""
    if len(prices) < period:
        return None
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return round(ema, 2)


def calculate_bollinger_bands(prices: List[float], period: int = 20) -> Optional[Dict]:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: List of closing prices
        period: Period for calculation (default 20)
        
    Returns:
        Dict with upper, middle, lower bands
    """
    if len(prices) < period:
        return None
    
    # Calculate SMA (middle band)
    sma = sum(prices[-period:]) / period
    
    # Calculate standard deviation
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std_dev = variance ** 0.5
    
    # Bands
    upper_band = sma + (2 * std_dev)
    lower_band = sma - (2 * std_dev)
    
    current_price = prices[-1]
    
    # Position within bands
    band_width = upper_band - lower_band
    position = ((current_price - lower_band) / band_width) * 100 if band_width > 0 else 50
    
    return {
        "upper": round(upper_band, 2),
        "middle": round(sma, 2),
        "lower": round(lower_band, 2),
        "position": round(position, 2),
        "signal": "Near upper band" if position > 80 else "Near lower band" if position < 20 else "Mid-range"
    }


def calculate_momentum(prices: List[float], period: int = 10) -> Optional[float]:
    """Calculate price momentum."""
    if len(prices) < period:
        return None
    
    momentum = ((prices[-1] - prices[-period]) / prices[-period]) * 100
    return round(momentum, 2)


async def get_crypto_technical_analysis(symbol: str, current_data: Dict, stream_writer=None) -> Dict:
    """
    Get comprehensive technical analysis for a cryptocurrency.
    
    Args:
        symbol: Trading pair
        current_data: Current price data from exchanges
        
    Returns:
        Dict with technical analysis data
    """
    # Emit progress: fetching historical data
    if stream_writer:
        stream_writer({"type": "custom", "step": "technical_analysis", "status": "fetching_historical"})
    
    # Fetch historical data
    historical = await fetch_historical_data(symbol, days=7)
    
    # Emit progress: calculating indicators
    if stream_writer:
        stream_writer({"type": "custom", "step": "technical_analysis", "status": "calculating_indicators"})
    
    if not historical or len(historical) < 20:
        return {
            "status": "limited_data",
            "message": "Insufficient historical data for technical analysis"
        }
    
    # Extract closing prices
    closes = [c["close"] for c in historical]
    volumes = [c["volume"] for c in historical]
    
    # Calculate indicators
    rsi = calculate_rsi(closes)
    ma_20 = calculate_moving_average(closes, 20)
    ma_50 = calculate_moving_average(closes, 50)
    ema_12 = calculate_ema(closes, 12)
    ema_26 = calculate_ema(closes, 26)
    macd = calculate_macd(closes)
    bollinger = calculate_bollinger_bands(closes, 20)
    momentum = calculate_momentum(closes, 10)
    volatility = calculate_volatility(closes[-24:])  # Last 24 hours
    
    # Current price
    current_price = current_data.get("average_price", closes[-1])
    
    # Support/Resistance
    sr_levels = find_support_resistance(historical, current_price)
    
    # Price change calculations
    price_24h_ago = closes[-24] if len(closes) >= 24 else closes[0]
    price_7d_ago = closes[0]
    
    change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
    change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
    
    # Volume trend
    avg_volume_recent = sum(volumes[-24:]) / min(24, len(volumes))
    avg_volume_older = sum(volumes[-48:-24]) / min(24, len(volumes) - 24) if len(volumes) > 24 else avg_volume_recent
    volume_trend = "increasing" if avg_volume_recent > avg_volume_older else "decreasing"
    
    # RSI interpretation
    if rsi:
        if rsi > 70:
            rsi_signal = "Overbought"
        elif rsi < 30:
            rsi_signal = "Oversold"
        else:
            rsi_signal = "Neutral"
    else:
        rsi_signal = "N/A"
    
    # MA trend
    if ma_20 and ma_50:
        if current_price > ma_20 > ma_50:
            ma_trend = "Strong Uptrend"
        elif current_price < ma_20 < ma_50:
            ma_trend = "Strong Downtrend"
        elif current_price > ma_20:
            ma_trend = "Short-term Bullish"
        else:
            ma_trend = "Short-term Bearish"
    else:
        ma_trend = "N/A"
    
    # Market structure analysis
    price_range_24h = sr_levels["recent_high"] - sr_levels["recent_low"]
    price_position = ((current_price - sr_levels["recent_low"]) / price_range_24h * 100) if price_range_24h > 0 else 50
    
    # Trend strength
    if ma_20 and ma_50:
        trend_strength = abs(((ma_20 - ma_50) / ma_50) * 100)
    else:
        trend_strength = 0
    
    return {
        "status": "success",
        "symbol": symbol,
        "current_price": current_price,
        "technical_indicators": {
            "rsi": rsi,
            "rsi_signal": rsi_signal,
            "ma_20": ma_20,
            "ma_50": ma_50,
            "ema_12": ema_12,
            "ema_26": ema_26,
            "ma_trend": ma_trend,
            "macd": macd,
            "bollinger_bands": bollinger,
            "momentum": momentum,
            "volatility": volatility,
            "trend_strength": round(trend_strength, 2)
        },
        "price_action": {
            "change_24h": round(change_24h, 2),
            "change_7d": round(change_7d, 2),
            "support": sr_levels["support"],
            "resistance": sr_levels["resistance"],
            "recent_high": sr_levels["recent_high"],
            "recent_low": sr_levels["recent_low"],
            "price_position_in_range": round(price_position, 2)
        },
        "volume_analysis": {
            "trend": volume_trend,
            "avg_recent": round(avg_volume_recent, 2),
            "avg_older": round(avg_volume_older, 2),
            "volume_change_pct": round(((avg_volume_recent - avg_volume_older) / avg_volume_older * 100), 2) if avg_volume_older > 0 else 0
        },
        "timestamp": datetime.now().isoformat()
    }


def format_technical_analysis(tech_data: Dict, current_data: Dict) -> str:
    """
    Format technical analysis for AI context.
    
    Args:
        tech_data: Technical analysis data
        current_data: Current price data
        
    Returns:
        Formatted string for AI context
    """
    if tech_data.get("status") != "success":
        return "Technical analysis data unavailable."
    
    symbol = tech_data.get("symbol", "")
    price = tech_data.get("current_price", 0)
    ti = tech_data.get("technical_indicators", {})
    pa = tech_data.get("price_action", {})
    va = tech_data.get("volume_analysis", {})
    
    # Get exchange data
    exchanges = current_data.get("exchanges", [])
    total_volume = current_data.get("total_volume_24h_usd", 0)
    
    analysis_text = f"""
REAL-TIME TECHNICAL ANALYSIS DATA FOR {symbol}:

Current Market Data:
├─ Price: ${price:,.2f}
├─ 24h Change: {pa.get('change_24h', 0):+.2f}%
├─ 7d Change: {pa.get('change_7d', 0):+.2f}%
└─ Total 24h Volume: ${total_volume:,.0f}

Exchange Prices:
"""
    
    for ex in exchanges[:3]:
        analysis_text += f"├─ {ex['exchange']}: ${ex['price']:,.2f}\n"
    
    # Get additional indicators
    macd = ti.get('macd', {})
    bollinger = ti.get('bollinger_bands', {})
    
    # RSI interpretation
    rsi_val = ti.get('rsi', 0)
    if rsi_val > 70:
        rsi_interp = "Overbought (>70)"
    elif rsi_val < 30:
        rsi_interp = "Oversold (<30)"
    else:
        rsi_interp = "Neutral (30-70)"
    
    # Format Bollinger values
    bb_upper = f"${bollinger.get('upper', 0):,.2f}" if bollinger else "N/A"
    bb_middle = f"${bollinger.get('middle', 0):,.2f}" if bollinger else "N/A"
    bb_lower = f"${bollinger.get('lower', 0):,.2f}" if bollinger else "N/A"
    bb_signal = bollinger.get('signal', 'N/A') if bollinger else 'N/A'
    
    # Format MACD values
    macd_signal = macd.get('signal', 'N/A') if macd else 'N/A'
    macd_value = macd.get('macd', 'N/A') if macd else 'N/A'
    
    analysis_text += f"""
Technical Indicators:
├─ RSI (14): {ti.get('rsi', 'N/A')} - {ti.get('rsi_signal', 'N/A')}
│  └─ Interpretation: {rsi_interp}
├─ Moving Averages:
│  ├─ MA(20): ${ti.get('ma_20', 0):,.2f}
│  ├─ MA(50): ${ti.get('ma_50', 0):,.2f}
│  ├─ EMA(12): ${ti.get('ema_12', 0):,.2f}
│  ├─ EMA(26): ${ti.get('ema_26', 0):,.2f}
│  └─ Trend: {ti.get('ma_trend', 'N/A')} (Strength: {ti.get('trend_strength', 0):.2f}%)
├─ MACD: {macd_signal}
│  └─ Value: {macd_value}
├─ Bollinger Bands:
│  ├─ Upper: {bb_upper}
│  ├─ Middle: {bb_middle}
│  ├─ Lower: {bb_lower}
│  └─ Position: {bb_signal}
├─ Momentum (10-period): {ti.get('momentum', 'N/A')}%
└─ Volatility: {ti.get('volatility', 0):.2f}%

Price Levels & Structure:
├─ Current: ${price:,.2f}
├─ Support: ${pa.get('support', 0):,.2f} ({abs(price - pa.get('support', price)):.2f} below)
├─ Resistance: ${pa.get('resistance', 0):,.2f} ({pa.get('resistance', price) - price:.2f} above)
├─ 7d High: ${pa.get('recent_high', 0):,.2f}
├─ 7d Low: ${pa.get('recent_low', 0):,.2f}
├─ Position in Range: {pa.get('price_position_in_range', 50):.1f}%
└─ Distance to High: {abs(price - pa.get('recent_high', price)):.2f} ({abs((price - pa.get('recent_high', price))/price*100):.2f}%)

Volume Analysis:
├─ Trend: {va.get('trend', 'N/A').capitalize()}
├─ Volume Change: {va.get('volume_change_pct', 0):+.2f}%
└─ Interpretation: {'Strong buying pressure' if va.get('volume_change_pct', 0) > 20 else 'Weak participation' if va.get('volume_change_pct', 0) < -20 else 'Normal activity'}

CRITICAL: Use this REAL-TIME data in your analysis. Base your analysis on these actual numbers.
When discussing price levels, support/resistance, or trends, reference these specific values.
"""
    
    return analysis_text


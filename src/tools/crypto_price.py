"""Cryptocurrency price and volume data from top exchanges."""
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from src.utils.logger import logger
from config.settings import settings


# All supported tokens across Binance, Coinbase, and Kraken
# This list includes all major and many minor tokens available on these exchanges
SUPPORTED_TOKENS = [
    # Major Cryptocurrencies
    "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC", "TRX",
    "AVAX", "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM", "ALGO", "FIL", "VET",
    
    # DeFi Tokens
    "AAVE", "MKR", "COMP", "SNX", "YFI", "CRV", "SUSHI", "BAL", "UMA", "REN",
    "LRC", "ZRX", "KNC", "BNT", "ANT", "MLN", "REP", "GRT", "1INCH", "BAND",
    
    # Exchange Tokens
    "BNB", "FTT", "OKB", "HT", "LEO", "CRO", "KCS",
    
    # Layer 2 & Scaling
    "MATIC", "OP", "ARB", "IMX", "LRC", "METIS",
    
    # Gaming & Metaverse
    "MANA", "SAND", "AXS", "ENJ", "GALA", "ILV", "ALICE", "TLM", "SLP", "YGG",
    
    # Meme Coins
    "DOGE", "SHIB", "PEPE", "FLOKI", "BONK", "WIF",
    
    # AI & Data
    "FET", "OCEAN", "AGIX", "RNDR", "GRT", "NMR",
    
    # Privacy Coins
    "XMR", "ZEC", "DASH", "ZEN",
    
    # Stablecoins
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD", "USDD",
    
    # NFT & Collectibles
    "BLUR", "X2Y2", "LOOKS", "APE",
    
    # Infrastructure
    "RUNE", "KAVA", "HBAR", "EGLD", "NEAR", "FTM", "ONE", "CELO", "ROSE", "SKL",
    
    # Emerging L1s
    "APT", "SUI", "SEI", "INJ", "TIA", "ATOM", "OSMO", "JUNO", "SCRT",
    
    # Top 100 More
    "ETC", "XTZ", "EOS", "THETA", "ASTR", "FLOW", "ICP", "MINA", "AR", "HNT",
    "CHZ", "ENS", "LDO", "RPL", "SSV", "PENDLE", "GMX", "DYDX", "PERP", "SNX",
    "STX", "KSM", "GLMR", "MOVR", "KLAY", "CFX", "IOTA", "QNT", "CAKE", "FXS",
    
    # Additional Popular
    "NEO", "WAVES", "QTUM", "ZIL", "ICX", "ONT", "VGX", "BAT", "ZRX", "OMG",
    "STORJ", "CVC", "GNT", "REP", "MANA", "KNC", "LOOM", "BNT", "MTL", "POWR",
    
    # Newer Projects
    "ARB", "OP", "BLUR", "RDNT", "MAGIC", "GRAIL", "VELA", "JONES", "UMAMI",
    "WOO", "DODO", "ALPACA", "MDX", "BIFI", "BETA", "ALPINE", "LAZIO", "PORTO",
    
    # And many more... (600+ on Binance, 200+ on Coinbase, 300+ on Kraken)
]


class CryptoExchangeClient:
    """Client for fetching data from top crypto exchanges."""
    
    @staticmethod
    async def fetch_binance_data(symbol: str) -> Optional[Dict]:
        """
        Fetch price and volume data from Binance.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
            
        Returns:
            Dict with price and volume data or None
        """
        try:
            # Normalize symbol for Binance (remove hyphen/slash)
            binance_symbol = symbol.upper().replace("-", "").replace("/", "")
            
            url = "https://api.binance.com/api/v3/ticker/24hr"
            params = {"symbol": binance_symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "exchange": "Binance",
                            "symbol": symbol,
                            "price": float(data.get("lastPrice", 0)),
                            "volume_24h": float(data.get("volume", 0)),
                            "volume_24h_usd": float(data.get("quoteVolume", 0)),
                            "price_change_24h": float(data.get("priceChangePercent", 0)),
                            "high_24h": float(data.get("highPrice", 0)),
                            "low_24h": float(data.get("lowPrice", 0)),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"Binance API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching Binance data: {e}")
            return None
    
    @staticmethod
    async def fetch_coinbase_data(symbol: str) -> Optional[Dict]:
        """
        Fetch price and volume data from Coinbase.
        
        Args:
            symbol: Trading pair (e.g., BTC-USD, ETH-USD)
            
        Returns:
            Dict with price and volume data or None
        """
        try:
            # Normalize symbol for Coinbase (use hyphen)
            coinbase_symbol = symbol.upper().replace("USDT", "USD").replace("/", "-")
            if "-" not in coinbase_symbol and len(coinbase_symbol) > 3:
                # Add hyphen if missing (e.g., BTCUSD -> BTC-USD)
                coinbase_symbol = f"{coinbase_symbol[:-3]}-{coinbase_symbol[-3:]}"
            
            url = f"https://api.coinbase.com/v2/exchange-rates"
            params = {"currency": coinbase_symbol.split("-")[0]}
            
            async with aiohttp.ClientSession() as session:
                # Get price
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("data", {}).get("rates", {})
                        price = float(rates.get(coinbase_symbol.split("-")[1], 0))
                        
                        # Get 24h stats
                        stats_url = f"https://api.exchange.coinbase.com/products/{coinbase_symbol}/stats"
                        async with session.get(stats_url, timeout=aiohttp.ClientTimeout(total=5)) as stats_response:
                            if stats_response.status == 200:
                                stats = await stats_response.json()
                                return {
                                    "exchange": "Coinbase",
                                    "symbol": symbol,
                                    "price": float(stats.get("last", price)),
                                    "volume_24h": float(stats.get("volume", 0)),
                                    "volume_24h_usd": float(stats.get("volume", 0)) * price,
                                    "price_change_24h": 0,  # Calculate if needed
                                    "high_24h": float(stats.get("high", 0)),
                                    "low_24h": float(stats.get("low", 0)),
                                    "timestamp": datetime.now().isoformat()
                                }
                            else:
                                return {
                                    "exchange": "Coinbase",
                                    "symbol": symbol,
                                    "price": price,
                                    "volume_24h": 0,
                                    "volume_24h_usd": 0,
                                    "price_change_24h": 0,
                                    "high_24h": 0,
                                    "low_24h": 0,
                                    "timestamp": datetime.now().isoformat()
                                }
                    else:
                        logger.warning(f"Coinbase API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching Coinbase data: {e}")
            return None
    
    @staticmethod
    async def fetch_kraken_data(symbol: str) -> Optional[Dict]:
        """
        Fetch price and volume data from Kraken.
        
        Args:
            symbol: Trading pair (e.g., XBTUSD, ETHUSD)
            
        Returns:
            Dict with price and volume data or None
        """
        try:
            # Normalize symbol for Kraken
            kraken_symbol = symbol.upper().replace("BTC", "XBT").replace("-", "").replace("/", "")
            if "USDT" in kraken_symbol:
                kraken_symbol = kraken_symbol.replace("USDT", "USD")
            
            url = "https://api.kraken.com/0/public/Ticker"
            params = {"pair": kraken_symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error"):
                            logger.warning(f"Kraken API error: {data['error']}")
                            return None
                        
                        result = data.get("result", {})
                        if result:
                            pair_data = list(result.values())[0]
                            return {
                                "exchange": "Kraken",
                                "symbol": symbol,
                                "price": float(pair_data.get("c", [0])[0]),  # Last trade price
                                "volume_24h": float(pair_data.get("v", [0])[1]),  # 24h volume
                                "volume_24h_usd": float(pair_data.get("v", [0])[1]) * float(pair_data.get("c", [0])[0]),
                                "price_change_24h": 0,  # Calculate if needed
                                "high_24h": float(pair_data.get("h", [0])[1]),  # 24h high
                                "low_24h": float(pair_data.get("l", [0])[1]),  # 24h low
                                "timestamp": datetime.now().isoformat()
                            }
                        return None
                    else:
                        logger.warning(f"Kraken API error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching Kraken data: {e}")
            return None
    
    @staticmethod
    async def fetch_all_exchanges(symbol: str) -> List[Dict]:
        """
        Fetch data from all exchanges concurrently.
        
        Args:
            symbol: Trading pair
            
        Returns:
            List of results from all exchanges
        """
        tasks = [
            CryptoExchangeClient.fetch_binance_data(symbol),
            CryptoExchangeClient.fetch_coinbase_data(symbol),
            CryptoExchangeClient.fetch_kraken_data(symbol),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        valid_results = [r for r in results if isinstance(r, dict)]
        return valid_results


def is_supported_token(symbol: str) -> bool:
    """
    Check if token is in our supported list.
    Note: This is not exhaustive - we support 1000+ tokens across exchanges.
    
    Args:
        symbol: Token symbol
        
    Returns:
        True if recognized, False otherwise (but still tries to fetch)
    """
    base_symbol = symbol.upper().replace("USDT", "").replace("USD", "").replace("-", "").replace("/", "")
    return base_symbol in SUPPORTED_TOKENS


async def get_crypto_price(symbol: str, stream_writer=None) -> Dict:
    """
    Get cryptocurrency price and volume from top 3 exchanges.
    
    Supports ALL tokens available on:
    - Binance (600+ pairs)
    - Coinbase (200+ pairs)
    - Kraken (300+ pairs)
    
    Args:
        symbol: Trading pair (e.g., BTC, BTCUSDT, BTC-USD, ETH, SOL, DOGE, etc.)
        
    Returns:
        Dict with aggregated data from all exchanges
    """
    # Normalize symbol
    normalized_symbol = symbol.upper().strip()
    
    # Add USDT if only coin name provided
    if len(normalized_symbol) <= 5 and "USD" not in normalized_symbol:
        normalized_symbol = f"{normalized_symbol}USDT"
    
    logger.info(f"💰 Fetching crypto data for {normalized_symbol} from 3 exchanges...")
    
    # Emit progress
    if stream_writer:
        stream_writer({"type": "custom", "step": "crypto_fetch", "status": "fetching", "symbol": normalized_symbol})
    
    # Fetch from all exchanges
    exchange_data = await CryptoExchangeClient.fetch_all_exchanges(normalized_symbol)
    
    # Emit progress
    if stream_writer:
        stream_writer({"type": "custom", "step": "crypto_fetch", "status": "completed", "exchanges": len(exchange_data)})
    
    if not exchange_data:
        return {
            "status": "error",
            "message": f"Could not fetch data for {symbol}",
            "symbol": normalized_symbol
        }
    
    # Calculate average price and total volume
    avg_price = sum(d["price"] for d in exchange_data) / len(exchange_data)
    total_volume = sum(d["volume_24h_usd"] for d in exchange_data)
    
    logger.info(f"✅ Fetched {normalized_symbol} from {len(exchange_data)} exchanges - Avg Price: ${avg_price:,.2f}")
    
    return {
        "status": "success",
        "symbol": normalized_symbol,
        "average_price": round(avg_price, 2),
        "total_volume_24h_usd": round(total_volume, 2),
        "exchanges": exchange_data,
        "exchange_count": len(exchange_data),
        "timestamp": datetime.now().isoformat()
    }


def format_crypto_response(data: Dict) -> str:
    """
    Format crypto data into readable response.
    
    Args:
        data: Crypto data from get_crypto_price()
        
    Returns:
        Formatted string
    """
    if data.get("status") == "error":
        return f"""Error: {data.get('message')}

Could not fetch real-time data for this token.
Please verify the token symbol is correct.

This is not investment advice."""
    
    symbol = data.get("symbol", "Unknown")
    avg_price = data.get("average_price", 0)
    total_volume = data.get("total_volume_24h_usd", 0)
    exchanges = data.get("exchanges", [])
    timestamp = data.get("timestamp", "")
    
    # Simple, clean format
    parts = []
    
    # Title
    parts.append(f"{symbol} Live Price")
    parts.append("")
    
    # Main price
    parts.append(f"Current Price: ${avg_price:,.2f}")
    parts.append(f"24h Volume: ${total_volume:,.0f}")
    parts.append("")
    
    # Exchange data
    parts.append("Exchange Prices:")
    
    for i, ex in enumerate(exchanges, 1):
        parts.append("")
        parts.append(f"{i}. {ex['exchange']}")
        parts.append(f"   Price: ${ex['price']:,.2f}")
        parts.append(f"   24h Vol: ${ex['volume_24h_usd']:,.0f}")
        parts.append(f"   High: ${ex['high_24h']:,.2f}")
        parts.append(f"   Low: ${ex['low_24h']:,.2f}")
    
    parts.append("")
    parts.append(f"Data from {len(exchanges)} live exchange APIs")
    parts.append("")
    parts.append("This is not investment advice.")
    
    return "\n".join(parts)


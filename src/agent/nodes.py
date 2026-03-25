"""Agent nodes for LangGraph."""
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.state import AgentState
from src.agent.retro_commands import check_retro_command
from src.tools.crypto_price import get_crypto_price, format_crypto_response
from src.tools.crypto_analysis import get_crypto_technical_analysis, format_technical_analysis
from src.tools.onchain import record_inference
from src.utils.logger import logger
from src.utils.model_factory import get_model
from config.settings import settings
from config.prompts import ROUTER_PROMPT, RESPONSE_PROMPT
from config.response_rules import format_response_with_disclaimer
import asyncio


async def router_node(state: AgentState) -> AgentState:
    """Route user query to appropriate handler."""
    import time
    start_time = time.time()
    
    # Get stream writer if available
    config = state.get("__config__", {})
    stream_writer = config.get("stream_writer")
    
    # Emit custom event: routing started
    if stream_writer:
        stream_writer({"type": "custom", "step": "routing", "status": "started"})
    
    # Get last message
    if not state.get("messages"):
        state["is_simple_question"] = True
        return state
    
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Check for retro commands first
    retro_result = check_retro_command(query)
    if retro_result:
        state["is_simple_question"] = True
        state["current_task"] = "retro_command"
        state["retro_command_response"] = retro_result["response"]
        state["performance_metrics"] = {"router_time": time.time() - start_time}
        logger.info(f"Retro command detected: {retro_result['metadata']['type']}")
        return state
    
    # Simple classification
    query_lower = query.lower()
    
    # Check for DIRECT crypto price queries only
    # Only trigger crypto tool if explicitly asking for price/volume
    direct_price_keywords = ["price", "cost", "worth", "value", "volume", "how much"]
    has_price_keyword = any(keyword in query_lower for keyword in direct_price_keywords)
    
    # Words that indicate general question (should go to AI)
    ai_required_keywords = ["analysis", "analyze", "why", "how does", "explain", 
                            "what is", "should", "will", "forecast", "predict",
                            "compare", "better", "good", "bad", "invest", "buy", "sell"]
    needs_ai = any(keyword in query_lower for keyword in ai_required_keywords)
    
    # Only use crypto tool if asking for price AND not asking general question
    if has_price_keyword and not needs_ai:
        # Extract potential symbol from query - need smarter detection
        words = query.split()
        
        # Common English words that should NEVER be treated as crypto symbols
        excluded_words = {
            "WHAT", "IS", "THE", "AND", "OR", "FOR", "OF", "TO", "IN", "IT", "ON", "AT", "BY", "AS",
            "ARE", "WAS", "WERE", "BEEN", "BE", "HAVE", "HAS", "HAD", "DO", "DOES", "DID",
            "A", "AN", "THIS", "THAT", "THESE", "THOSE", "I", "YOU", "HE", "SHE", "WE", "THEY",
            "MY", "YOUR", "HIS", "HER", "ITS", "OUR", "THEIR", "ME", "HIM", "US", "THEM",
            "CAN", "COULD", "WILL", "WOULD", "SHALL", "SHOULD", "MAY", "MIGHT", "MUST",
            "NOT", "NO", "YES", "BUT", "IF", "THEN", "THAN", "SO", "VERY", "TOO", "ALSO",
            "PRICE", "VOLUME", "SHOW", "TELL", "GIVE", "GET", "HOW", "MUCH", "MANY", "SOME",
            "ABOUT", "AROUND", "BETWEEN", "THROUGH", "DURING", "BEFORE", "AFTER", "ABOVE",
            "BELOW", "FROM", "UP", "DOWN", "OUT", "OFF", "OVER", "UNDER", "AGAIN", "FURTHER",
            "THEN", "ONCE", "HERE", "THERE", "WHEN", "WHERE", "WHY", "ALL", "BOTH", "EACH",
            "FEW", "MORE", "MOST", "OTHER", "SUCH", "ONLY", "OWN", "SAME", "JUST", "NOW"
        }
        
        # Known crypto symbols (check these first for accuracy)
        known_cryptos = {
            "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC", "AVAX",
            "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM", "ALGO", "VET", "ICP", "FIL",
            "TRX", "ETC", "XTZ", "AAVE", "COMP", "MKR", "SNX", "SUSHI", "CRV", "YFI",
            "SHIB", "PEPE", "FLOKI", "APE", "SAND", "MANA", "AXS", "GALA", "ENJ",
            "OP", "ARB", "IMX", "BLUR", "GMX", "DYDX", "PENDLE", "LDO", "RPL"
        }
        
        for word in words:
            word_clean = word.upper().strip("?,.'\"!;:")
            
            # Skip if too short or too long
            if len(word_clean) < 2 or len(word_clean) > 10:
                continue
            
            # Skip if not alphanumeric
            if not word_clean.isalnum():
                continue
            
            # Skip common English words
            if word_clean in excluded_words:
                continue
            
            # Priority 1: Known crypto symbol
            if word_clean in known_cryptos:
                task_type = "crypto_price"
                is_simple = True
                state["crypto_symbol"] = word_clean
                state["current_task"] = task_type
                state["is_simple_question"] = is_simple
                state["performance_metrics"] = {"router_time": time.time() - start_time}
                logger.info(f"Crypto price query detected: {word_clean}")
                return state
            
            # Priority 2: Looks like crypto (short uppercase, ends with common patterns)
            if (len(word_clean) <= 6 and 
                (word_clean.endswith("USD") or word_clean.endswith("USDT") or 
                 word_clean.endswith("BTC") or word_clean.endswith("ETH") or
                 any(crypto in word_clean for crypto in known_cryptos))):
                task_type = "crypto_price"
                is_simple = True
                state["crypto_symbol"] = word_clean
                state["current_task"] = task_type
                state["is_simple_question"] = is_simple
                state["performance_metrics"] = {"router_time": time.time() - start_time}
                logger.info(f"Crypto price query detected: {word_clean}")
                return state
    
    # Detect task type based on keywords (English only)
    if any(word in query_lower for word in ["help", "support", "guide"]):
        task_type = "help"
        is_simple = True
    elif any(word in query_lower for word in ["hello", "hi", "hey", "greetings"]):
        task_type = "greeting"
        is_simple = True
    elif any(word in query_lower for word in ["calculate", "compute", "math", "solve"]):
        task_type = "calculation"
        is_simple = False
    elif any(word in query_lower for word in ["time", "date", "clock", "timezone"]):
        task_type = "time"
        is_simple = True
    elif any(word in query_lower for word in ["analyze", "analysis", "research", "study", "investigate"]):
        task_type = "analysis"
        is_simple = False
    elif any(word in query_lower for word in ["code", "program", "debug", "develop"]):
        task_type = "programming"
        is_simple = False
    elif any(word in query_lower for word in ["explain", "what", "why", "how"]):
        task_type = "explanation"
        is_simple = False
    else:
        task_type = "general"
        is_simple = len(query.split()) < 15
    
    state["current_task"] = task_type
    state["is_simple_question"] = is_simple
    
    elapsed = time.time() - start_time
    state["performance_metrics"] = {"router_time": elapsed}
    
    # Emit update event: router completed
    if stream_writer:
        stream_writer({
            "type": "update",
            "node": "router",
            "data": {
                "task_type": task_type,
                "is_simple": is_simple,
                "elapsed": elapsed
            }
        })
    
    logger.info(f"Router: {task_type} (simple={is_simple}) in {elapsed:.3f}s")
    return state


async def quick_response_node(state: AgentState) -> AgentState:
    """Generate quick response for simple questions."""
    import time
    start_time = time.time()
    
    # Check if this is a retro command
    if state.get("retro_command_response"):
        # Use pre-generated retro command response
        response_content = state["retro_command_response"]
        state["messages"].append(AIMessage(content=response_content))
        
        elapsed = time.time() - start_time
        state["performance_metrics"]["quick_response_time"] = elapsed
        logger.info(f"Retro command response in {elapsed:.3f}s")
        return state
    
    # Check if this is a crypto price query OR analysis with crypto symbol
    if state.get("crypto_symbol"):
        symbol = state["crypto_symbol"]
        logger.info(f"Fetching REAL-TIME crypto price for {symbol}")
        
        # Get stream writer
        config = state.get("__config__", {})
        stream_writer = config.get("stream_writer")
        
        # CRITICAL: Fetch crypto data from LIVE APIs ONLY
        crypto_data = await get_crypto_price(symbol, stream_writer)
        
        # If just price query, return formatted price
        if state.get("current_task") == "crypto_price":
            response_content = format_crypto_response(crypto_data)
            state["messages"].append(AIMessage(content=response_content))
            state["tool_results"]["crypto_price"] = crypto_data
            
            elapsed = time.time() - start_time
            state["performance_metrics"]["quick_response_time"] = elapsed
            logger.info(f"Real-time crypto price response in {elapsed:.3f}s")
            return state
        
        # If analysis/explanation task, store price data and continue to AI
        else:
            state["tool_results"]["crypto_price"] = crypto_data
            logger.info(f"Fetched price data for AI analysis: ${crypto_data.get('average_price', 0):,.2f}")
            # Continue to AI with price data
    
    # If crypto analysis, check for symbol
    if state.get("current_task") in ["analysis", "explanation", "general"]:
        # Check if query mentions a crypto symbol
        query = state["messages"][-1].content if state.get("messages") else ""
        query_lower = query.lower()
        
        known_cryptos = {
            "BTC", "BITCOIN", "ETH", "ETHEREUM", "BNB", "XRP", "ADA", "SOL", "SOLANA",
            "DOGE", "DOGECOIN", "DOT", "MATIC", "POLYGON", "AVAX", "AVALANCHE",
            "LINK", "CHAINLINK", "UNI", "UNISWAP"
        }
        
        words = query.split()
        for word in words:
            word_clean = word.upper().strip("?,.'\"!;:")
            if word_clean in known_cryptos:
                # Fetch price AND technical data for context
                logger.info(f"Detected crypto in analysis query: {word_clean}")
                try:
                    # Get stream writer
                    config = state.get("__config__", {})
                    stream_writer = config.get("stream_writer")
                    
                    # Fetch current price data with progress
                    crypto_data = await get_crypto_price(word_clean, stream_writer)
                    state["tool_results"]["crypto_price"] = crypto_data
                    state["crypto_symbol"] = word_clean
                    
                    # Fetch technical analysis data
                    logger.info(f"Fetching technical analysis for {word_clean}...")
                    try:
                        tech_analysis = await get_crypto_technical_analysis(word_clean, crypto_data, stream_writer)
                        state["tool_results"]["technical_analysis"] = tech_analysis
                        logger.info(f"✅ Technical analysis completed for {word_clean}")
                    except Exception as tech_error:
                        logger.warning(f"Technical analysis failed: {tech_error}")
                        state["tool_results"]["technical_analysis"] = {"status": "limited_data"}
                    
                    logger.info(f"Fetched complete data for {word_clean}")
                except Exception as e:
                    logger.warning(f"Could not fetch {word_clean} data: {e}")
                break
    
    query = state["messages"][-1].content if state.get("messages") else ""
    
    # Get model
    model = get_model(
        model_name=settings.fast_model,
        provider=settings.llm_provider,
        fast_mode=True
    )
    
    # Generate response
    from langchain_core.messages import SystemMessage, HumanMessage
    from config.prompts import SYSTEM_PROMPT
    
    # Build context with crypto data if available
    context_parts = [SYSTEM_PROMPT]
    
    # Add comprehensive crypto analysis data to context if available
    if state.get("tool_results", {}).get("crypto_price"):
        crypto_data = state["tool_results"]["crypto_price"]
        tech_data = state.get("tool_results", {}).get("technical_analysis")
        
        if crypto_data.get("status") == "success":
            # Add current price context
            symbol = crypto_data.get("symbol", "")
            avg_price = crypto_data.get("average_price", 0)
            volume = crypto_data.get("total_volume_24h_usd", 0)
            exchanges = crypto_data.get("exchanges", [])
            
            price_context = f"""

REAL-TIME MARKET DATA (Use this current data in your analysis):
Symbol: {symbol}
Current Price: ${avg_price:,.2f}
24h Volume: ${volume:,.0f}
Data from {len(exchanges)} exchanges (Binance, Coinbase, Kraken)

Exchange Prices:
"""
            for ex in exchanges:
                price_context += f"{ex['exchange']}: ${ex['price']:,.2f} | High: ${ex['high_24h']:,.2f} | Low: ${ex['low_24h']:,.2f}\n"
            
            context_parts.append(price_context)
            
            # Add technical analysis if available
            if tech_data and tech_data.get("status") == "success":
                tech_context = format_technical_analysis(tech_data, crypto_data)
                context_parts.append(tech_context)
                
                # Add analysis instructions
                analysis_instructions = """

ANALYSIS GUIDELINES:
1. Start with current price and key metrics
2. Interpret RSI signal (overbought >70, oversold <30, neutral 30-70)
3. Discuss MA trend and what it indicates
4. Mention support/resistance levels for context
5. Comment on volume trend (increasing = more interest)
6. Give 2-3 sentence summary of technical outlook
7. Keep response concise and actionable
8. Use bullet points for clarity
9. Reference the actual numbers provided above

Format your response as:
- Current market situation (price, volume)
- Technical indicators (RSI, MA, trend)
- Key levels (support, resistance)
- Volume analysis
- Brief outlook/summary

DO NOT make up numbers. Use ONLY the data provided above."""
                context_parts.append(analysis_instructions)
    
    system_content = "\n".join(context_parts)
    
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=query)
    ]
    
    # Check if streaming is enabled and stream writer is available
    config = state.get("__config__", {})
    stream_writer = config.get("stream_writer")
    
    if stream_writer and settings.streaming_enabled:
        # Streaming mode - stream tokens
        full_response = ""
        async for chunk in model.astream(messages):
            if chunk.content:
                full_response += chunk.content
                # Stream token
                stream_writer({
                    "type": "token",
                    "content": chunk.content
                })
        
        # Add disclaimer
        response_content = format_response_with_disclaimer(full_response)
    else:
        # Non-streaming mode
        response = await model.ainvoke(messages)
        response_content = format_response_with_disclaimer(response.content)
    
    state["messages"].append(AIMessage(content=response_content))

    # Fire-and-forget: record inference proof on Base Mainnet (never blocks response)
    asyncio.ensure_future(
        record_inference(
            prompt=query,
            result=response_content,
            session_id=state.get("session_id"),
        )
    )

    elapsed = time.time() - start_time
    state["performance_metrics"]["quick_response_time"] = elapsed

    logger.info(f"Quick response in {elapsed:.3f}s")
    return state


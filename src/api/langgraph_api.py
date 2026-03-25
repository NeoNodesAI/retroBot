"""LangGraph Cloud API compatible endpoints for Warden App integration."""
from fastapi import APIRouter, HTTPException, Header, Body, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import uuid
from datetime import datetime, timezone

from src.agent.graph import get_agent
from src.agent.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage
from src.utils.logger import logger

router = APIRouter(tags=["langgraph"])


def verify_warden_auth(authorization: Optional[str], privy_id_token: Optional[str]) -> bool:
    """
    Verify Warden Protocol authentication.
    
    Args:
        authorization: Bearer token from Authorization header
        privy_id_token: Privy ID token from privy-id-token header
        
    Returns:
        True if authenticated (or auth disabled), False otherwise
    """
    # For now, accept all requests (optional auth)
    # In production, implement proper JWT verification
    if authorization or privy_id_token:
        logger.info(f"🔑 Warden auth present: Bearer={bool(authorization)}, Privy={bool(privy_id_token)}")
    return True


def is_valid_assistant_id(assistant_id: str) -> bool:
    """
    Check if assistant_id is valid.
    
    Args:
        assistant_id: Assistant ID from request
        
    Returns:
        True if valid, False otherwise
    """
    return assistant_id in ALLOWED_ASSISTANT_IDS

# Fixed assistant IDs (support multiple for compatibility)
ASSISTANT_ID = "retrobot-warden-001"
ALLOWED_ASSISTANT_IDS = {
    "retrobot-warden-001",  # Our default
    "wrapper",              # Warden's default
    "agent",                # Generic
    "retrobot",             # Short form
}

# Thread storage (in-memory)
_threads: Dict[str, List[Dict]] = {}
_runs: Dict[str, Dict] = {}


class LangGraphRunRequest(BaseModel):
    """LangGraph Cloud API run request format."""
    assistant_id: str
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class LangGraphRunResponse(BaseModel):
    """LangGraph Cloud API run response format."""
    run_id: str
    assistant_id: str
    status: str
    output: Dict[str, Any]
    error: Optional[str] = None


def convert_langgraph_messages(input_data: Dict) -> List:
    """Convert LangGraph input format to LangChain messages.
    
    Supports multiple formats:
    - Standard: {"role": "user", "content": "text"}
    - Warden App: {"type": "human", "content": "text", "id": "...", "createdAt": "..."}
    - Legacy: {"role": "human", "content": "text"}
    - Multimodal: {"role": "user", "content": [{"type": "text", "text": "..."}]}
    """
    messages = []
    
    if not isinstance(input_data, dict):
        logger.warning(f"Invalid input_data type: {type(input_data)}")
        return messages
    
    if "messages" in input_data and isinstance(input_data["messages"], list):
        for msg in input_data["messages"]:
            if not isinstance(msg, dict):
                continue
            
            # Get role - support both "role" and "type" fields
            # Warden uses "type": "human" or "type": "ai"
            role = msg.get("role") or msg.get("type", "user")
            
            # Normalize role names
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            
            content = msg.get("content", "")
            
            # Handle multimodal content
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text" and "text" in part:
                            text_parts.append(part["text"])
                        elif "content" in part:
                            text_parts.append(str(part["content"]))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = " ".join(text_parts) if text_parts else ""
            
            if not isinstance(content, str):
                content = str(content) if content else ""
            
            # Skip empty messages
            if not content.strip():
                logger.warning(f"Skipping empty message with role: {role}")
                continue
            
            # Log Warden-specific fields for debugging
            if msg.get("id"):
                logger.debug(f"Warden message ID: {msg.get('id')}")
            if msg.get("createdAt"):
                logger.debug(f"Warden message created: {msg.get('createdAt')}")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    logger.info(f"Converted {len(messages)} messages from input")
    return messages


def convert_to_langgraph_output(state: AgentState, existing_history: List = None, include_history: bool = False, response_only: bool = False, warden_format: bool = True) -> Dict:
    """Convert agent state to LangGraph output format.
    
    Args:
        state: Agent state
        existing_history: Existing conversation history
        include_history: If True, include full history
        response_only: If True, return only assistant response (no user message duplication)
        warden_format: If True, use Warden Protocol format with extra fields
    
    Returns:
        Output dict with messages
    """
    output = {}
    output_messages = []
    
    if include_history and existing_history:
        # Include full history
        for msg in existing_history:
            if isinstance(msg, dict) and "role" in msg:
                output_messages.append(msg)
    
    # Extract messages from state
    if "messages" in state and state["messages"]:
        # Include current turn messages (user + assistant, but NOT history)
        # Track content to avoid duplicates
        seen_contents = set()
        if output_messages:
            for existing_msg in output_messages:
                content = existing_msg.get("content", "")
                msg_type = existing_msg.get("type") or existing_msg.get("role")
                seen_contents.add((msg_type, content))
        
        for msg in state["messages"]:
            if hasattr(msg, 'content'):
                new_msg = None
                msg_type = None
                
                if isinstance(msg, HumanMessage):
                    msg_type = "human" if warden_format else "user"
                    # Check for duplicate content
                    if (msg_type, msg.content) in seen_contents:
                        continue
                    
                    if warden_format:
                        # Warden format with extra fields
                        new_msg = {
                            "type": "human",
                            "content": msg.content,
                            "id": str(uuid.uuid4()),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "additional_kwargs": {},
                            "response_metadata": {}
                        }
                    else:
                        new_msg = {"role": "user", "content": msg.content}
                    seen_contents.add((msg_type, msg.content))
                    
                elif isinstance(msg, AIMessage):
                    msg_type = "ai" if warden_format else "assistant"
                    # Check for duplicate content
                    if (msg_type, msg.content) in seen_contents:
                        continue
                    
                    if warden_format:
                        # Warden format with extra fields
                        new_msg = {
                            "type": "ai",
                            "content": msg.content,
                            "id": f"run-{uuid.uuid4()}",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "additional_kwargs": {},
                            "response_metadata": {},
                            "tool_calls": [],
                            "invalid_tool_calls": []
                        }
                    else:
                        new_msg = {"role": "assistant", "content": msg.content}
                    seen_contents.add((msg_type, msg.content))
                
                if new_msg:
                    output_messages.append(new_msg)
    
    output["messages"] = output_messages
    
    # Add Warden-specific fields if enabled
    if warden_format:
        output["ui"] = []
        output["multiChainBalances"] = {}
        output["selectedChainId"] = None
        output["messariAccepted"] = False
        output["wachaiAccepted"] = False
        output["whitelistedTokens"] = False
        output["proofsOfInference"] = []
        output["paymentRequests"] = []
        
        # Add wrappedAgent if agent info available
        agent_address = state.get("agent_address") or "eip155:8453:0x52B6159BAAddB249fa5b913A46B161930284Dad3"
        output["wrappedAgent"] = {
            "agentAddress": agent_address,
            "agentSource": "external",
            "monetization": "inference"
        }
    else:
        output["metadata"] = {
            "task_type": state.get("current_task"),
            "session_id": state.get("session_id"),
        }
    
    return output


def get_full_conversation(state: AgentState, existing_history: List = None, warden_format: bool = True) -> List:
    """Get full conversation including history (for thread storage).
    
    Args:
        state: Agent state
        existing_history: Existing conversation history
        warden_format: If True, use Warden Protocol format
        
    Returns:
        Full message list with history
    """
    all_messages = []
    seen_contents = set()
    
    # Add existing history
    if existing_history:
        for msg in existing_history:
            if isinstance(msg, dict) and ("role" in msg or "type" in msg):
                all_messages.append(msg)
                # Track to avoid duplicates
                content = msg.get("content", "")
                msg_type = msg.get("type") or msg.get("role")
                seen_contents.add((msg_type, content))
    
    # Add new messages (avoid duplicates)
    if "messages" in state and state["messages"]:
        for msg in state["messages"]:
            if hasattr(msg, 'content'):
                new_msg = None
                msg_type = None
                
                if isinstance(msg, HumanMessage):
                    msg_type = "human" if warden_format else "user"
                    # Skip if duplicate
                    if (msg_type, msg.content) in seen_contents:
                        continue
                    
                    if warden_format:
                        new_msg = {
                            "type": "human",
                            "content": msg.content,
                            "id": str(uuid.uuid4()),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "additional_kwargs": {},
                            "response_metadata": {}
                        }
                    else:
                        new_msg = {"role": "user", "content": msg.content}
                    seen_contents.add((msg_type, msg.content))
                    
                elif isinstance(msg, AIMessage):
                    msg_type = "ai" if warden_format else "assistant"
                    # Skip if duplicate
                    if (msg_type, msg.content) in seen_contents:
                        continue
                    
                    if warden_format:
                        new_msg = {
                            "type": "ai",
                            "content": msg.content,
                            "id": f"run-{uuid.uuid4()}",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "additional_kwargs": {},
                            "response_metadata": {},
                            "tool_calls": [],
                            "invalid_tool_calls": []
                        }
                    else:
                        new_msg = {"role": "assistant", "content": msg.content}
                    seen_contents.add((msg_type, msg.content))
                
                if new_msg:
                    all_messages.append(new_msg)
    
    return all_messages


# ==================== ASSISTANTS ENDPOINTS ====================

@router.get("/assistants")
@router.get("/langgraph/assistants")
async def list_assistants():
    """List all assistants - direct array return."""
    return [{
        "assistant_id": ASSISTANT_ID,
        "graph_id": "retrobot",
        "created_at": "2024-01-01T00:00:00.000000+00:00",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "config": {},
        "metadata": {"created_by": "system"},
        "version": 1,
        "name": "retroBot",
        "description": "NeoNodes AI agent",
        "context": {}
    }]


@router.get("/assistants/{assistant_id}")
@router.get("/langgraph/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """Get assistant information."""
    if not is_valid_assistant_id(assistant_id):
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return {
        "assistant_id": ASSISTANT_ID,
        "graph_id": "retrobot",
        "name": "retroBot",
        "description": "NeoNodes AI agent",
        "status": "active"
    }


@router.get("/assistants/search")
@router.post("/assistants/search")
@router.get("/agents/search")
@router.post("/agents/search")
@router.get("/langgraph/assistants/search")
@router.post("/langgraph/assistants/search")
async def search_assistants(query: Optional[str] = None, limit: int = 10, offset: int = 0):
    """Search assistants - supports GET and POST."""
    assistant = {
        "assistant_id": ASSISTANT_ID,
        "graph_id": "retrobot",
        "name": "retroBot",
        "description": "NeoNodes AI agent"
    }
    
    if not query:
        return [assistant]
    
    query_lower = query.lower()
    if query_lower in assistant["name"].lower() or query_lower in assistant["description"].lower():
        return [assistant]
    
    return []


# ==================== THREADS ENDPOINTS ====================

@router.get("/threads")
@router.get("/langgraph/threads")
async def list_threads():
    """List all threads - direct array return."""
    threads_list = []
    for thread_id, messages in _threads.items():
        if isinstance(messages, list):
            threads_list.append({
                "thread_id": thread_id,
                "created_at": datetime.now().isoformat(),
                "metadata": {"message_count": len(messages)}
            })
    return threads_list


@router.post("/threads")
@router.post("/langgraph/threads")
async def create_thread():
    """Create a new thread."""
    thread_id = str(uuid.uuid4())
    _threads[thread_id] = []
    logger.info(f"Created new thread: {thread_id}")
    
    return {
        "thread_id": thread_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {}
    }


@router.get("/threads/{thread_id}")
@router.get("/langgraph/threads/{thread_id}")
async def get_thread(thread_id: str):
    """Get thread details."""
    if thread_id not in _threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = _threads[thread_id]
    if not isinstance(messages, list):
        messages = []
        _threads[thread_id] = []
    
    return {
        "thread_id": thread_id,
        "messages": messages,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {"message_count": len(messages)}
    }


@router.delete("/threads/{thread_id}")
@router.delete("/langgraph/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a thread."""
    if thread_id not in _threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    del _threads[thread_id]
    
    # Clean up runs
    runs_to_delete = [run_id for run_id, run in _runs.items() if run.get("thread_id") == thread_id]
    for run_id in runs_to_delete:
        del _runs[run_id]
    
    return {"status": "deleted", "thread_id": thread_id}


@router.patch("/threads/{thread_id}")
@router.patch("/langgraph/threads/{thread_id}")
async def update_thread(thread_id: str, metadata: Dict[str, Any] = Body(...)):
    """Update thread metadata (Warden App compatible)."""
    if thread_id not in _threads:
        _threads[thread_id] = []
        logger.info(f"Auto-created thread for metadata update: {thread_id}")
    
    return {
        "thread_id": thread_id,
        "metadata": metadata,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/threads/search")
@router.post("/threads/search")
@router.get("/langgraph/threads/search")
@router.post("/langgraph/threads/search")
async def search_threads(query: Optional[str] = None, limit: int = 10, offset: int = 0):
    """Search threads (Warden App compatible)."""
    threads_list = []
    for thread_id, messages in _threads.items():
        if isinstance(messages, list):
            # If query provided, search in messages
            if query:
                query_lower = query.lower()
                found = any(
                    query_lower in msg.get("content", "").lower()
                    for msg in messages
                    if isinstance(msg, dict)
                )
                if not found:
                    continue
            
            threads_list.append({
                "thread_id": thread_id,
                "created_at": datetime.now().isoformat(),
                "metadata": {"message_count": len(messages)}
            })
    
    # Apply pagination
    return threads_list[offset:offset + limit]


@router.get("/threads/{thread_id}/runs")
@router.get("/langgraph/threads/{thread_id}/runs")
async def list_thread_runs(thread_id: str, limit: int = 10, offset: int = 0):
    """List runs for a thread - direct array return."""
    if thread_id not in _threads:
        _threads[thread_id] = []
        logger.info(f"Auto-created thread: {thread_id}")
    
    # Find runs for this thread
    thread_runs = [r for r in _runs.values() if r.get("thread_id") == thread_id]
    thread_runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return thread_runs[offset:offset + limit]


@router.get("/threads/{thread_id}/state")
@router.post("/threads/{thread_id}/state")
@router.get("/langgraph/threads/{thread_id}/state")
@router.post("/langgraph/threads/{thread_id}/state")
async def get_thread_state(thread_id: str, state_update: Optional[Dict[str, Any]] = Body(None)):
    """Get/Update thread state (CRITICAL for RemoteGraph)."""
    if thread_id not in _threads:
        _threads[thread_id] = []
        logger.info(f"Auto-created thread: {thread_id}")
    
    # If POST with state update
    if state_update:
        values = state_update.get("values", {})
        if "messages" in values and isinstance(values["messages"], list):
            _threads[thread_id] = values["messages"]
            logger.info(f"Updated thread state: {thread_id}")
    
    messages = _threads[thread_id]
    if not isinstance(messages, list):
        messages = []
    
    return {
        "values": {"messages": messages},
        "next": [],
        "config": {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": str(uuid.uuid4())
            }
        },
        "metadata": {
            "source": "update",
            "step": len(messages),
            "writes": None
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parent_config": None
    }


@router.get("/threads/{thread_id}/history")
@router.post("/threads/{thread_id}/history")
@router.get("/langgraph/threads/{thread_id}/history")
@router.post("/langgraph/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    """Get thread history (CRITICAL for Warden App)."""
    if thread_id not in _threads:
        return []
    
    messages = _threads[thread_id]
    if not isinstance(messages, list):
        messages = []
    
    return [{
        "values": {"messages": messages},
        "next": [],
        "config": {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": str(uuid.uuid4())
            }
        },
        "metadata": {
            "source": "update",
            "step": len(messages),
            "writes": None
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parent_config": None
    }]


# ==================== RUNS ENDPOINTS ====================

@router.post("/runs/wait")
@router.post("/langgraph/runs/wait")
async def create_run_wait(
    request: LangGraphRunRequest,
    authorization: Optional[str] = Header(None),
    privy_id_token: Optional[str] = Header(None, alias="privy-id-token")
):
    """Create run and wait for output.
    
    Accepts Authorization and privy-id-token headers for Warden Protocol.
    """
    logger.info(f"📨 Incoming request to /runs/wait")
    
    # Verify authentication (optional for now)
    verify_warden_auth(authorization, privy_id_token)
    
    if not is_valid_assistant_id(request.assistant_id):
        logger.warning(f"❌ Invalid assistant_id: {request.assistant_id}")
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    logger.info(f"✅ Valid assistant_id: {request.assistant_id}")
    
    try:
        agent = get_agent()
        messages = convert_langgraph_messages(request.input)
        
        # Get thread_id
        thread_id = None
        if request.config and "configurable" in request.config:
            thread_id = request.config["configurable"].get("thread_id")
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = _threads.get(thread_id, [])
        
        # Build state
        state: AgentState = {
            "messages": messages,
            "conversation_history": conversation_history,
            "user_context": {},
            "session_id": thread_id,
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
        }
        
        # Run agent
        result = await agent.ainvoke(state, config=request.config or {})
        
        # Convert to output (only NEW messages, no history)
        output = convert_to_langgraph_output(result, existing_history=None, include_history=False, response_only=False)
        
        # Save FULL conversation to thread (with history)
        full_conversation = get_full_conversation(result, conversation_history)
        _threads[thread_id] = full_conversation
        
        run_id = str(uuid.uuid4())
        
        logger.info(f"✅ Request completed successfully (run_id: {run_id[:8]}...)")
        
        return LangGraphRunResponse(
            run_id=run_id,
            assistant_id=ASSISTANT_ID,
            status="success",
            output=output
        )
    
    except Exception as e:
        logger.error(f"❌ Error in run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/stream")
@router.post("/langgraph/runs/stream")
async def create_run_stream(
    request_body: LangGraphRunRequest,
    authorization: Optional[str] = Header(None),
    privy_id_token: Optional[str] = Header(None, alias="privy-id-token")
):
    """Create run with streaming output - includes token streaming.
    
    Accepts Authorization and privy-id-token headers for Warden Protocol.
    """
    if not is_valid_assistant_id(request_body.assistant_id):
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    logger.info(f"✅ Valid assistant_id: {request_body.assistant_id}")
    
    # Verify authentication (optional for now)
    verify_warden_auth(authorization, privy_id_token)
    
    input_data = request_body.input
    config_data = request_body.config or {}
    
    # Token buffer for streaming
    token_buffer = []
    
    def stream_writer(data: dict):
        """Custom stream writer for token streaming."""
        token_buffer.append(data)
    
    async def generate():
        try:
            agent = get_agent()
            messages = convert_langgraph_messages(input_data)
            
            thread_id = None
            if config_data and "configurable" in config_data:
                thread_id = config_data["configurable"].get("thread_id")
            
            if not thread_id:
                thread_id = str(uuid.uuid4())
            
            conversation_history = _threads.get(thread_id, [])
            
            state: AgentState = {
                "messages": messages,
                "conversation_history": conversation_history,
                "user_context": {},
                "session_id": thread_id,
                "user_preferences": {},
                "current_task": None,
                "task_history": [],
                "is_simple_question": None,
                "tool_results": {},
                "performance_metrics": {},
                "errors": [],
                "out_of_scope": None,
                "scope_reason": None,
                "scope_redirect_message": None,
                "last_provider_used": None,
                "query_complexity": None,
                "crypto_symbol": None,
                "__config__": {"stream_writer": stream_writer}
            }
            
            run_id = str(uuid.uuid4())
            
            # Extract user messages for initial events (Warden format)
            user_messages_list = []
            logger.info(f"Converting {len(messages)} messages for initial values event")
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    user_messages_list.append({
                        "type": "human",
                        "content": msg.content,
                        "id": str(uuid.uuid4()),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "additional_kwargs": {},
                        "response_metadata": {}
                    })
                    logger.info(f"Added user message: {msg.content[:50]}")
            
            # If no messages extracted, try different approach
            if not user_messages_list:
                # Extract from input_data directly
                if input_data.get("messages"):
                    for msg in input_data["messages"]:
                        if isinstance(msg, dict):
                            msg_type = msg.get("type") or msg.get("role")
                            if msg_type in ["user", "human"]:
                                user_messages_list.append({
                                    "type": "human",
                                    "content": msg.get("content", ""),
                                    "id": msg.get("id", str(uuid.uuid4())),
                                    "created_at": msg.get("createdAt") or msg.get("created_at") or datetime.now(timezone.utc).isoformat(),
                                    "additional_kwargs": msg.get("additional_kwargs", {}),
                                    "response_metadata": msg.get("response_metadata", {})
                                })
            
            logger.info(f"User messages for values event: {len(user_messages_list)}")
            
            # 1. Metadata event
            yield f"event: metadata\ndata: {json.dumps({'run_id': run_id, 'thread_id': thread_id})}\n\n"
            
            # 2. Initial values event (with user message - Warden format)
            initial_values = {
                "messages": user_messages_list,
                "ui": [],
                "multiChainBalances": {},
                "selectedChainId": None,
                "messariAccepted": False,
                "wachaiAccepted": False,
                "whitelistedTokens": False,
                "proofsOfInference": [],
                "paymentRequests": []
            }
            yield f"event: values\ndata: {json.dumps(initial_values)}\n\n"
            
            # 3. Status update: running
            yield f"event: updates\ndata: {json.dumps({'status': 'running'})}\n\n"
            
            # 5. Execute agent
            result = await agent.ainvoke(state, config=config_data)
            
            # 6. Values after routing (with user message - Warden format)
            router_values = {
                "messages": user_messages_list,
                "ui": [],
                "multiChainBalances": {},
                "selectedChainId": None,
                "messariAccepted": False,
                "wachaiAccepted": False,
                "whitelistedTokens": False,
                "proofsOfInference": [],
                "paymentRequests": []
            }
            yield f"event: values\ndata: {json.dumps(router_values)}\n\n"
            
            # 7. Status update: running
            yield f"event: updates\ndata: {json.dumps({'status': 'running'})}\n\n"
            
            # Stream tokens as they come
            if token_buffer:
                for token_data in token_buffer:
                    if token_data.get("type") == "token":
                        yield f"event: messages/token\ndata: {json.dumps({'content': token_data['content']})}\n\n"
            output = convert_to_langgraph_output(result, existing_history=None, include_history=False, response_only=False)
            
            # 6. Messages/partial (assistant only)
            if output.get("messages"):
                for msg in output["messages"]:
                    if msg.get("role") == "assistant" and msg.get("content"):
                        yield f"event: messages/partial\ndata: {json.dumps([{'type': 'ai', 'content': msg['content']}])}\n\n"
            
            # 7. Messages/complete (assistant only)
            if output.get("messages"):
                for msg in output["messages"]:
                    if msg.get("role") == "assistant" and msg.get("content"):
                        yield f"event: messages/complete\ndata: {json.dumps([{'type': 'ai', 'content': msg['content']}])}\n\n"
            
            # 8. Status: processing
            yield f"event: updates\ndata: {json.dumps({'status': 'processing'})}\n\n"
            
            # 9. Final values (user + assistant)
            yield f"event: values\ndata: {json.dumps(output)}\n\n"
            
            # 10. Status: running
            yield f"event: updates\ndata: {json.dumps({'status': 'running'})}\n\n"
            
            # Save FULL conversation to thread (with history)
            full_conversation = get_full_conversation(result, conversation_history)
            _threads[thread_id] = full_conversation
            
            # 11. Debug (with correct message count)
            debug_data = {
                "run_id": run_id,
                "thread_id": thread_id,
                "message_count": len(output.get("messages", [])),
                "status": "success",
                "performance": result.get("performance_metrics", {})
            }
            yield f"event: debug\ndata: {json.dumps(debug_data)}\n\n"
            
            # 12. Done (user + assistant)
            yield f"event: done\ndata: {json.dumps(output)}\n\n"
            
            # 13. End
            yield f"event: end\ndata: null\n\n"
        
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    # Warden Protocol compatible response headers
    temp_thread_id = str(uuid.uuid4())
    temp_run_id = str(uuid.uuid4())
    
    headers = {
        "Cache-Control": "no-store",
        "Content-Location": f"/threads/{temp_thread_id}/runs/{temp_run_id}",
        "Location": f"/threads/{temp_thread_id}/runs/{temp_run_id}/stream",
    }
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers=headers
    )


@router.post("/threads/{thread_id}/runs")
@router.post("/langgraph/threads/{thread_id}/runs")
async def create_thread_run(
    thread_id: str, 
    request_body: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None),
    privy_id_token: Optional[str] = Header(None, alias="privy-id-token")
):
    """Create a run for a specific thread.
    
    Accepts Authorization and privy-id-token headers for Warden Protocol.
    """
    # Verify authentication (optional for now)
    verify_warden_auth(authorization, privy_id_token)
    if thread_id not in _threads:
        _threads[thread_id] = []
        logger.info(f"Auto-created thread: {thread_id}")
    
    try:
        agent = get_agent()
        input_data = request_body.get("input", {})
        messages = convert_langgraph_messages(input_data)
        conversation_history = _threads.get(thread_id, [])
        
        state: AgentState = {
            "messages": messages,
            "conversation_history": conversation_history,
            "user_context": {},
            "session_id": thread_id,
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
        }
        
        result = await agent.ainvoke(state)
        
        # Output: only NEW ASSISTANT response (no user message, no history)
        output = convert_to_langgraph_output(result, existing_history=None, include_history=False, response_only=False)
        
        # Storage: FULL conversation with history
        full_conversation = get_full_conversation(result, conversation_history)
        _threads[thread_id] = full_conversation
        
        run_id = str(uuid.uuid4())
        _runs[run_id] = {
            "run_id": run_id,
            "thread_id": thread_id,
            "assistant_id": ASSISTANT_ID,
            "status": "success",
            "output": output,
            "created_at": datetime.now().isoformat()
        }
        
        return _runs[run_id]
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/{thread_id}/runs/stream")
@router.post("/langgraph/threads/{thread_id}/runs/stream")
async def create_thread_run_stream(
    thread_id: str, 
    request_body: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None),
    privy_id_token: Optional[str] = Header(None, alias="privy-id-token"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Create a streaming run for a thread (CRITICAL for Warden App).
    
    Supports Warden App format with stream_mode, if_not_exists, etc.
    Accepts Authorization and privy-id-token headers for Warden Protocol.
    
    Warden payload format:
    {
      "input": {"messages": [{"type": "human", "content": "...", "id": "...", "createdAt": "..."}]},
      "metadata": {"privy-id-token": "...", "addresses": [], "agentAddress": "..."},
      "stream_mode": ["values", "messages-tuple", "custom"],
      "stream_resumable": true,
      "assistant_id": "wrapper",
      "on_disconnect": "continue"
    }
    """
    # Extract metadata (Warden-specific)
    metadata = request_body.get("metadata", {})
    if metadata:
        # Get privy-id-token from metadata if not in header
        if not privy_id_token and metadata.get("privy-id-token"):
            privy_id_token = metadata.get("privy-id-token")
        
        # Log Warden-specific metadata
        if metadata.get("agentAddress"):
            logger.info(f"🏦 Warden agent address: {metadata.get('agentAddress')}")
        if metadata.get("addresses"):
            logger.info(f"💼 User addresses: {len(metadata.get('addresses', []))} addresses")
    
    # Verify authentication (optional for now)
    verify_warden_auth(authorization, privy_id_token)
    
    # Check assistant_id if provided
    assistant_id = request_body.get("assistant_id")
    if assistant_id and not is_valid_assistant_id(assistant_id):
        logger.warning(f"❌ Invalid assistant_id: {assistant_id}")
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    if assistant_id:
        logger.info(f"✅ Valid assistant_id: {assistant_id}")
    # Handle if_not_exists parameter (Warden App)
    if_not_exists = request_body.get("if_not_exists", "create")
    
    if thread_id not in _threads:
        if if_not_exists == "create":
            _threads[thread_id] = []
            logger.info(f"Auto-created thread: {thread_id}")
        else:
            raise HTTPException(status_code=404, detail="Thread not found")
    
    input_data = request_body.get("input", {})
    config_data = request_body.get("config", {})
    
    # Streaming buffers (all modes)
    token_buffer = []
    update_buffer = []
    custom_buffer = []
    
    def stream_writer(data: dict):
        """Custom stream writer for all streaming modes."""
        data_type = data.get("type", "custom")
        
        if data_type == "token":
            token_buffer.append(data)
        elif data_type == "update":
            update_buffer.append(data)
        elif data_type == "custom":
            custom_buffer.append(data)
        else:
            custom_buffer.append(data)
    
    async def generate():
        try:
            agent = get_agent()
            messages = convert_langgraph_messages(input_data)
            conversation_history = _threads.get(thread_id, [])
            
            state: AgentState = {
                "messages": messages,
                "conversation_history": conversation_history,
                "user_context": {},
                "session_id": thread_id,
                "user_preferences": {},
                "current_task": None,
                "task_history": [],
                "is_simple_question": None,
                "tool_results": {},
                "performance_metrics": {},
                "errors": [],
                "out_of_scope": None,
                "scope_reason": None,
                "scope_redirect_message": None,
                "last_provider_used": None,
                "query_complexity": None,
                "crypto_symbol": None,
                "__config__": {"stream_writer": stream_writer}
            }
            
            run_id = str(uuid.uuid4())
            _runs[run_id] = {
                "run_id": run_id,
                "thread_id": thread_id,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Extract user messages for initial events
            user_messages_list = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    user_messages_list.append({"role": "user", "content": msg.content})
            
            # Fallback: extract from input_data
            if not user_messages_list and input_data.get("messages"):
                for msg in input_data["messages"]:
                    if isinstance(msg, dict) and msg.get("role") in ["user", "human"]:
                        user_messages_list.append({"role": "user", "content": msg.get("content", "")})
            
            # 1. Metadata event
            yield f"event: metadata\ndata: {json.dumps({'run_id': run_id, 'thread_id': thread_id})}\n\n"
            
            # 2. Initial values event (with user message - Warden format)
            initial_values = {
                "messages": user_messages_list,
                "metadata": {
                    "task": None,
                    "session_id": thread_id,
                    "metrics": {}
                }
            }
            yield f"event: values\ndata: {json.dumps(initial_values)}\n\n"
            
            # 3. Status update: running
            yield f"event: updates\ndata: {json.dumps({'status': 'running'})}\n\n"
            
            _runs[run_id]["status"] = "running"
            
            # 4. Status update: processing
            yield f"event: updates\ndata: {json.dumps({'status': 'processing'})}\n\n"
            
            # 5. Execute agent and stream everything
            result = await agent.ainvoke(state, config=config_data)
            
            # 6. Values after routing (with user message - Warden format)
            router_values = {
                "messages": user_messages_list,
                "ui": [],
                "multiChainBalances": {},
                "selectedChainId": None,
                "messariAccepted": False,
                "wachaiAccepted": False,
                "whitelistedTokens": False,
                "proofsOfInference": [],
                "paymentRequests": []
            }
            yield f"event: values\ndata: {json.dumps(router_values)}\n\n"
            
            # 7. Status update: running
            yield f"event: updates\ndata: {json.dumps({'status': 'running'})}\n\n"
            
            # Stream custom events (progress updates)
            if custom_buffer:
                for custom_data in custom_buffer:
                    yield f"event: custom\ndata: {json.dumps(custom_data)}\n\n"
            
            # Stream state updates (node outputs)
            if update_buffer:
                for update_data in update_buffer:
                    yield f"event: updates\ndata: {json.dumps(update_data)}\n\n"
            
            # Stream tokens as they arrive
            if token_buffer:
                for token_data in token_buffer:
                    if token_data.get("type") == "token":
                        yield f"event: messages/token\ndata: {json.dumps({'content': token_data['content']})}\n\n"
            
            output = convert_to_langgraph_output(result, existing_history=None, include_history=False, response_only=False)
            
            # 8. Messages/partial
            if output.get("messages"):
                for msg in output["messages"]:
                    if msg.get("role") == "assistant" and msg.get("content"):
                        yield f"event: messages/partial\ndata: {json.dumps([{'type': 'ai', 'content': msg['content']}])}\n\n"
            
            # 9. Messages/complete
            if output.get("messages"):
                for msg in output["messages"]:
                    if msg.get("role") == "assistant" and msg.get("content"):
                        yield f"event: messages/complete\ndata: {json.dumps([{'type': 'ai', 'content': msg['content']}])}\n\n"
            
            # 10. Status: processing
            yield f"event: updates\ndata: {json.dumps({'status': 'processing'})}\n\n"
            
            # 11. Final values
            yield f"event: values\ndata: {json.dumps(output)}\n\n"
            
            # 12. Status: running
            yield f"event: updates\ndata: {json.dumps({'status': 'running'})}\n\n"
            
            # Save FULL conversation to thread (with history)
            full_conversation = get_full_conversation(result, conversation_history)
            _threads[thread_id] = full_conversation
            
            _runs[run_id]["status"] = "success"
            _runs[run_id]["output"] = output
            _runs[run_id]["ended_at"] = datetime.now(timezone.utc).isoformat()
            
            # 13. Debug
            debug_data = {
                "run_id": run_id,
                "thread_id": thread_id,
                "message_count": len(output.get("messages", [])),
                "status": "success",
                "performance": result.get("performance_metrics", {})
            }
            yield f"event: debug\ndata: {json.dumps(debug_data)}\n\n"
            
            # 14. Done
            yield f"event: done\ndata: {json.dumps(output)}\n\n"
            
            # 15. End
            yield f"event: end\ndata: null\n\n"
        
        except Exception as e:
            logger.error(f"Stream error: {e}")
            if 'run_id' in locals() and run_id in _runs:
                _runs[run_id]["status"] = "error"
                _runs[run_id]["error"] = str(e)
            
            # Error event
            error_data = {
                "run_id": run_id if 'run_id' in locals() else None,
                "thread_id": thread_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    # Generate run_id for response headers
    temp_run_id = str(uuid.uuid4())
    
    # Warden Protocol compatible response headers
    headers = {
        "Cache-Control": "no-store",
        "Content-Location": f"/threads/{thread_id}/runs/{temp_run_id}",
        "Location": f"/threads/{thread_id}/runs/{temp_run_id}/stream",
    }
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers=headers
    )


@router.post("/threads/{thread_id}/state/checkpoint")
@router.post("/langgraph/threads/{thread_id}/state/checkpoint")
async def create_thread_checkpoint(thread_id: str, request_body: Dict[str, Any] = Body(default={})):
    """Create checkpoint for thread state (Warden App compatible)."""
    if thread_id not in _threads:
        _threads[thread_id] = []
        logger.info(f"Auto-created thread for checkpoint: {thread_id}")
    
    checkpoint_id = str(uuid.uuid4())
    
    return {
        "thread_id": thread_id,
        "checkpoint_id": checkpoint_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "values": {
            "messages": _threads.get(thread_id, [])
        }
    }


@router.post("/threads/state/bulk")
@router.post("/langgraph/threads/state/bulk")
async def bulk_update_thread_state(request_body: List[Dict[str, Any]] = Body(...)):
    """Bulk update thread states (Warden App compatible)."""
    results = []
    
    for update in request_body:
        thread_id = update.get("thread_id")
        if not thread_id:
            continue
        
        if thread_id not in _threads:
            _threads[thread_id] = []
        
        values = update.get("values", {})
        if "messages" in values and isinstance(values["messages"], list):
            _threads[thread_id] = values["messages"]
        
        results.append({
            "thread_id": thread_id,
            "checkpoint_id": str(uuid.uuid4()),
            "status": "updated"
        })
    
    return results


@router.post("/assistants/{assistant_id}/runs")
@router.post("/langgraph/assistants/{assistant_id}/runs")
async def create_assistant_run(
    assistant_id: str,
    request_body: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None),
    privy_id_token: Optional[str] = Header(None, alias="privy-id-token"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Create run for assistant (CRITICAL for RemoteGraph).
    
    Accepts Authorization and privy-id-token headers for Warden Protocol.
    """
    # Verify authentication (optional for now)
    verify_warden_auth(authorization, privy_id_token)
    
    if not is_valid_assistant_id(assistant_id):
        raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
    
    logger.info(f"✅ Valid assistant_id: {assistant_id}")
    
    try:
        agent = get_agent()
        input_data = request_body.get("input", {})
        config = request_body.get("config", {})
        
        # Get or create thread_id
        thread_id = None
        if config and "configurable" in config:
            thread_id = config["configurable"].get("thread_id")
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
            _threads[thread_id] = []
        
        messages = convert_langgraph_messages(input_data)
        conversation_history = _threads.get(thread_id, [])
        
        state: AgentState = {
            "messages": messages,
            "conversation_history": conversation_history,
            "user_context": {},
            "session_id": thread_id,
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
            "crypto_symbol": None,
        }
        
        result = await agent.ainvoke(state, config=config)
        output = convert_to_langgraph_output(result, conversation_history)
        
        if "messages" in output:
            _threads[thread_id] = output["messages"]
        
        run_id = str(uuid.uuid4())
        _runs[run_id] = {
            "run_id": run_id,
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "status": "success",
            "output": output,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        }
        
        return _runs[run_id]
        
    except Exception as e:
        logger.error(f"Error creating assistant run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}/runs/{run_id}")
@router.get("/langgraph/threads/{thread_id}/runs/{run_id}")
async def get_run(thread_id: str, run_id: str):
    """Get specific run details."""
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = _runs[run_id]
    if run.get("thread_id") != thread_id:
        raise HTTPException(status_code=404, detail="Run not found in this thread")
    
    return run


@router.get("/threads/{thread_id}/runs/{run_id}/wait")
@router.post("/threads/{thread_id}/runs/{run_id}/wait")
@router.get("/langgraph/threads/{thread_id}/runs/{run_id}/wait")
@router.post("/langgraph/threads/{thread_id}/runs/{run_id}/wait")
async def wait_for_run(thread_id: str, run_id: str):
    """Wait for run to complete (blocks until done)."""
    import asyncio
    
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = _runs[run_id]
    if run.get("thread_id") != thread_id:
        raise HTTPException(status_code=404, detail="Run not found in this thread")
    
    # Poll for completion (max 60 seconds)
    max_wait = 60
    interval = 0.5
    elapsed = 0
    
    while elapsed < max_wait:
        status = run.get("status")
        if status in ["success", "error", "timeout", "interrupted"]:
            return run
        
        await asyncio.sleep(interval)
        elapsed += interval
    
    # Timeout
    run["status"] = "timeout"
    return run


@router.post("/threads/{thread_id}/interrupt")
@router.post("/langgraph/threads/{thread_id}/interrupt")
async def interrupt_thread(thread_id: str):
    """Interrupt all running operations in thread."""
    if thread_id not in _threads:
        _threads[thread_id] = []
        logger.info(f"Auto-created thread: {thread_id}")
    
    # Find running runs for this thread
    interrupted_count = 0
    for run_id, run in _runs.items():
        if run.get("thread_id") == thread_id and run.get("status") == "running":
            run["status"] = "interrupted"
            run["ended_at"] = datetime.now(timezone.utc).isoformat()
            interrupted_count += 1
    
    logger.info(f"Interrupted {interrupted_count} runs in thread {thread_id}")
    
    return {
        "thread_id": thread_id,
        "interrupted_runs": interrupted_count,
        "status": "interrupted"
    }


@router.get("/assistants/{assistant_id}/crons")
@router.get("/langgraph/assistants/{assistant_id}/crons")
async def list_assistant_crons(assistant_id: str):
    """List cron jobs (not supported in self-hosted)."""
    return []


@router.post("/assistants/{assistant_id}/crons")
@router.post("/langgraph/assistants/{assistant_id}/crons")
async def create_assistant_cron(assistant_id: str, request_body: Dict[str, Any] = Body(...)):
    """Create cron job (not supported in self-hosted)."""
    raise HTTPException(
        status_code=501,
        detail="Cron jobs are not supported in self-hosted deployments. Use external cron scheduler."
    )


@router.get("/info")
async def get_server_info():
    """Get server information."""
    from config.settings import settings
    
    return {
        "version": settings.agent_version,
        "api_version": "v1",
        "server_type": "langgraph",
        "agent_name": settings.agent_name,
        "status": "running",
        "capabilities": {
            "streaming": True,
            "thread_management": True,
            "assistant_management": True,
            "crypto_data": True,
            "technical_analysis": True
        }
    }


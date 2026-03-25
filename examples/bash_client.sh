#!/bin/bash
# retroBot Bash Client Example

API_URL="http://173.212.220.240:8000"

echo "=== retroBot Bash Client ==="
echo ""

# Function to ask retroBot
ask_retrobot() {
    local question="$1"
    
    curl -s -X POST "${API_URL}/runs/wait" \
        -H "Content-Type: application/json" \
        -d "{
            \"assistant_id\": \"retrobot-warden-001\",
            \"input\": {
                \"messages\": [
                    {\"role\": \"user\", \"content\": \"${question}\"}
                ]
            }
        }" | jq -r '.output.messages[-1].content'
}

# Example 1: Simple question
echo "1. Simple Question:"
ask_retrobot "What is the price of BTC?"
echo ""
echo "=================================================="
echo ""

# Example 2: Retro command
echo "2. Retro Command:"
ask_retrobot "/retro status"
echo ""
echo "=================================================="
echo ""

# Example 3: Create thread and conversation
echo "3. Thread Conversation:"
THREAD_ID=$(curl -s -X POST "${API_URL}/threads" | jq -r '.thread_id')
echo "Created thread: $THREAD_ID"
echo ""

# First message
echo "Q: What is ETH price?"
curl -s -X POST "${API_URL}/threads/${THREAD_ID}/runs" \
    -H "Content-Type: application/json" \
    -d '{
        "input": {
            "messages": [
                {"role": "user", "content": "What is ETH price?"}
            ]
        }
    }' | jq -r '.output.messages[-1].content' | head -n 10
echo "..."
echo ""

# Follow-up message
echo "Q: What about SOL?"
curl -s -X POST "${API_URL}/threads/${THREAD_ID}/runs" \
    -H "Content-Type: application/json" \
    -d '{
        "input": {
            "messages": [
                {"role": "user", "content": "What about SOL?"}
            ]
        }
    }' | jq -r '.output.messages[-1].content' | head -n 10
echo "..."


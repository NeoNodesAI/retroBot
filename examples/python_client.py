"""
retroBot Python Client Example
"""
import requests
import json

API_URL = "http://173.212.220.240:8000"


def ask_retrobot(question):
    """Simple question to retroBot."""
    response = requests.post(
        f"{API_URL}/runs/wait",
        json={
            "assistant_id": "retrobot-warden-001",
            "input": {
                "messages": [
                    {"role": "user", "content": question}
                ]
            }
        },
        headers={"Content-Type": "application/json"}
    )
    return response.json()


def create_thread():
    """Create a conversation thread."""
    response = requests.post(f"{API_URL}/threads")
    return response.json()["thread_id"]


def send_message_to_thread(thread_id, message):
    """Send message in a thread (remembers context)."""
    response = requests.post(
        f"{API_URL}/threads/{thread_id}/runs",
        json={
            "input": {
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
        }
    )
    return response.json()


def main():
    print("=== retroBot Python Client ===\n")
    
    # Example 1: Simple question
    print("1. Simple Question:")
    result = ask_retrobot("What is the price of BTC?")
    messages = result["output"]["messages"]
    print(messages[-1]["content"])
    print("\n" + "="*50 + "\n")
    
    # Example 2: Retro command
    print("2. Retro Command:")
    result = ask_retrobot("/retro status")
    messages = result["output"]["messages"]
    print(messages[-1]["content"])
    print("\n" + "="*50 + "\n")
    
    # Example 3: Thread conversation
    print("3. Thread Conversation:")
    thread_id = create_thread()
    print(f"Created thread: {thread_id}\n")
    
    # First message
    result1 = send_message_to_thread(thread_id, "What is ETH price?")
    print("Q: What is ETH price?")
    print("A:", result1["output"]["messages"][-1]["content"][:200], "...\n")
    
    # Follow-up (context preserved)
    result2 = send_message_to_thread(thread_id, "What about SOL?")
    print("Q: What about SOL?")
    print("A:", result2["output"]["messages"][-1]["content"][:200], "...")


if __name__ == "__main__":
    main()


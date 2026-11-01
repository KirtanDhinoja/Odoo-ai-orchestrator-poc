import os
from dotenv import load_dotenv
load_dotenv()

from graph import app, SessionState

def run_demo():
    print("Starting Reelo AI Candidate PoC...")
    
    # Initialize empty session state
    state: SessionState = {
        "query": "",
        "user_type": "internal_sales",
        "user_state": "CA",
        "last_intent": None,
        "last_product_ids": [],
        "last_budget": None,
        "tool_outputs": {},
        "final_response": ""
    }

    while True:
        query = input("\nUser Query (or 'exit'): ")
        if query.lower() == 'exit':
            break
            
        state["query"] = query
        
        # Invoke LangGraph
        result = app.invoke(state)
        
        # Update state for next turn
        state = result
        
        print("\n=== AI RESPONSE ===")
        print(result["final_response"])
        print("===================\n")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY is missing in .env")
    else:
        run_demo()
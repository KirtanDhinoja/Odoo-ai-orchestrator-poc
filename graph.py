import os
import time
from typing import TypedDict, List, Optional, Any, Dict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from tools import hot_picks, compliance_filter, stock_by_warehouse, vendor_validate, kb_search
from logger import log_trace

class SessionState(TypedDict):
    query: str
    user_type: str
    user_state: str  # e.g., 'CA'
    last_intent: Optional[str]
    last_product_ids: List[int]
    last_budget: Optional[float]
    tool_outputs: Dict[str, Any]
    final_response: str

class IntentOutput(BaseModel):
    intent: str = Field(description="One of: SALES_RECO, COMPLIANCE_CHECK, VENDOR_ONBOARDING, OPS_STOCK, GENERAL_KB")
    extracted_budget: Optional[float] = Field(default=None)
    extracted_product_ids: List[int] = Field(default_factory=list)

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

def router_node(state: SessionState):
    start = time.time()
    structured_llm = llm.with_structured_output(IntentOutput)
    
    # Simple prompt injecting previous memory
    prompt = f"""
    Classify the query intent strictly into one of the allowed categories.
    
    DEFINITIONS:
    - SALES_RECO: User wants product recommendations or "hot picks" based on a budget.
    - COMPLIANCE_CHECK: User asks why a specific SKU/product is blocked, illegal, or unavailable in a state.
    - VENDOR_ONBOARDING: User asks about uploading catalogs, missing attributes (Net Wt, lab reports), or fixing product uploads.
    - OPS_STOCK: User asks about warehouse locations, inventory, or stock quantities.
    - GENERAL_KB: User asks about general return policies or shipping rules.
    
    Previous intent: {state.get('last_intent')}
    Previous product IDs: {state.get('last_product_ids')}
    Query: {state['query']}
    
    If the user refers to previous items (e.g., 'add 2 of the first one'), use the Previous product IDs.
    """
    
    result = structured_llm.invoke(prompt)
    
    # Update memory
    state["last_intent"] = result.intent
    if result.extracted_budget:
        state["last_budget"] = result.extracted_budget
    if result.extracted_product_ids:
        state["last_product_ids"] = result.extracted_product_ids
        
    log_trace(state["user_type"], result.intent, "router (LLM)", {"query": state["query"]}, (time.time() - start) * 1000, 150)
    return state

def executor_node(state: SessionState):
    start = time.time()
    intent = state["last_intent"]
    outputs = {}
    tool_called = "none"
    args = {}
    
    # Security Allowlist
    if intent == "VENDOR_ONBOARDING" and state["user_type"] == "portal_customer":
        outputs = {"error": "Unauthorized access to vendor tools."}
        state["tool_outputs"] = outputs
        return state

    # Canonical Chains Execution
    if intent == "SALES_RECO":
        budget = state.get("last_budget", 9999.0)
        picks = hot_picks(budget=budget)
        pids = [p["product_id"] for p in picks]
        outputs = compliance_filter(state["user_state"], pids)
        tool_called = "hot_picks -> compliance_filter"
        args = {"budget": budget, "state": state["user_state"]}
        state["last_product_ids"] = pids
        
    elif intent == "COMPLIANCE_CHECK":
        outputs = compliance_filter(state["user_state"], state.get("last_product_ids", []))
        tool_called = "compliance_filter"
        args = {"state": state["user_state"], "pids": state.get("last_product_ids")}
        
    elif intent == "OPS_STOCK":
        if state.get("last_product_ids"):
            outputs = stock_by_warehouse(state["last_product_ids"][0])
            tool_called = "stock_by_warehouse"
            args = {"pid": state["last_product_ids"][0]}
            
    elif intent == "VENDOR_ONBOARDING":
        # Mocking the JSON payload from the prompt query
        mock_payload = {"net_wt_oz": None, "lab_report_attached": False}
        outputs = vendor_validate(mock_payload)
        tool_called = "vendor_validate"
        
    elif intent == "GENERAL_KB":
        outputs = kb_search(state["query"])
        tool_called = "kb_search"

    state["tool_outputs"] = outputs
    log_trace(state["user_type"], intent, tool_called, args, (time.time() - start) * 1000, 0)
    return state

def formatter_node(state: SessionState):
    if "error" in state["tool_outputs"]:
        state["final_response"] = state["tool_outputs"]["error"]
        return state
        
    prompt = f"""
    You are an ERP assistant. Summarize this raw JSON tool output into a natural, helpful response.
    Do not invent facts. Only use the provided data.
    Raw Data: {state['tool_outputs']}
    """
    response = llm.invoke(prompt)
    state["final_response"] = response.content
    return state

# Compile Graph
workflow = StateGraph(SessionState)
workflow.add_node("router", router_node)
workflow.add_node("executor", executor_node)
workflow.add_node("formatter", formatter_node)

workflow.set_entry_point("router")
workflow.add_edge("router", "executor")
workflow.add_edge("executor", "formatter")
workflow.add_edge("formatter", END)

app = workflow.compile()
import json
import time
import uuid

def log_trace(user_type: str, intent: str, tool_name: str, args: dict, latency_ms: float, approx_tokens: int):
    trace = {
        "request_id": str(uuid.uuid4()),
        "user_type": user_type,
        "intent": intent,
        "tools_called": tool_name,
        "args": args,
        "latency_ms": round(latency_ms, 2),
        "approx_tokens": approx_tokens
    }
    print(f"\n[TRACE LOG] {json.dumps(trace)}\n")
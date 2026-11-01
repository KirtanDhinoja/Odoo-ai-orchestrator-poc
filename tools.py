from data_store import db

def hot_picks(budget: float, limit: int = 3) -> list:
    """Returns ranked products under budget, sorted by popularity."""
    affordable = [p for p in db.products_by_id.values() if p["price"] <= budget]
    sorted_picks = sorted(affordable, key=lambda x: x["popularity_score"], reverse=True)
    return sorted_picks[:limit]

def compliance_filter(state: str, product_ids: list[int]) -> dict:
    """Deterministic allow/block/review logic based on state."""
    result = {"allowed": [], "blocked": [], "review": []}
    for pid in product_ids:
        product = db.get_product_by_id(pid)
        if not product:
            continue
            
        if state in product.get("blocked_states", []):
            result["blocked"].append({"product_id": pid, "name": product["name"], "reason": f"BLOCKED_IN_{state}"})
        elif product.get("lab_report_required"):
            result["review"].append({"product_id": pid, "name": product["name"], "reason": "LAB_REPORT_REQUIRED"})
        else:
            result["allowed"].append(product)
    return result

def stock_by_warehouse(product_id: int) -> list:
    """Returns warehouse and quantity."""
    return [inv for inv in db.inventory if inv["product_id"] == product_id]

def vendor_validate(attributes: dict) -> dict:
    """Validates vendor onboarding payload."""
    missing = []
    if attributes.get("net_wt_oz") is None:
        missing.append("net_wt_oz")
    if not attributes.get("lab_report_attached"):
        missing.append("lab_report")
        
    if missing:
        return {"status": "FAIL", "missing_fields": missing, "required_documents": ["Lab Report"]}
    return {"status": "PASS", "missing_fields": [], "required_documents": []}

def kb_search(query: str) -> list:
    """Naive keyword search over KB docs."""
    query_lower = query.lower()
    return [doc for doc in db.kb_docs if query_lower in doc["text"].lower()]
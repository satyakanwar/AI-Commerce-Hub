import os, re
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import httpx

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")
client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=4000)
db = client["commerce_ai"]
app = FastAPI(title="Commerce AI Service")

@app.get("/health")
def health():
    client.admin.command("ping")
    return {"status": "ok", "service": "ai-service", "database": "mongodb"}

def get_products():
    try:
        r = httpx.get(f"{PRODUCT_SERVICE_URL}/products", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        raise HTTPException(503, "Product service is unavailable")

class ChatIn(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
def chat(payload: ChatIn):
    msg = payload.message.strip()
    if not msg:
        raise HTTPException(400, "Message cannot be empty")
    products = get_products()
    # Lightweight local intent/entity extraction and catalog-grounded response.
    budget_match = re.search(r"(?:under|below|less than|within)\s*₹?\s*([\d,]+)", msg.lower())
    budget = int(budget_match.group(1).replace(",", "")) if budget_match else None
    terms = [w for w in re.findall(r"[a-z0-9]+", msg.lower()) if len(w) > 2]
    ranked = []
    for p in products:
        haystack = f'{p["name"]} {p["category"]} {p["description"]}'.lower()
        score = sum(1 for term in terms if term in haystack)
        if budget is not None and float(p["price"]) <= budget:
            score += 3
        if budget is not None and float(p["price"]) > budget:
            score -= 4
        ranked.append((score, p))
    ranked.sort(key=lambda x: (x[0], -float(x[1]["price"])), reverse=True)
    matches = [p for score, p in ranked if score > 0][:3]
    if not matches:
        matches = [p for _, p in sorted(ranked, key=lambda x: float(x[1]["price"]))[:3]]
    answer = "Here are a few products that may fit your request:\n" + "\n".join(
        f'• {p["name"]} — ₹{float(p["price"]):,.0f} ({p["category"]})' for p in matches
    ) + "\nYou can open a product card to add it to your order."
    db.chat_messages.insert_one({"session_id": payload.session_id, "role": "user",
        "message": msg, "created_at": datetime.now(timezone.utc)})
    db.chat_messages.insert_one({"session_id": payload.session_id, "role": "assistant",
        "message": answer, "created_at": datetime.now(timezone.utc)})
    return {"reply": answer, "recommended_products": matches}

@app.get("/search")
def search(q: str):
    query = q.strip().lower()
    if not query:
        return {"query": q, "results": []}
    products = get_products()
    tokens = [w for w in re.findall(r"[a-z0-9]+", query) if len(w) > 1]
    ranked = []
    for p in products:
        text = f'{p["name"]} {p["category"]} {p["description"]}'.lower()
        score = sum(text.count(t) * (2 if t in p["name"].lower() else 1) for t in tokens)
        # Intent hints improve ranking for common shopping language.
        if any(x in query for x in ["cheap", "affordable", "budget"]):
            score += max(0, 5 - int(float(p["price"]) // 10000))
        if "camera" in query and "camera" in text:
            score += 4
        ranked.append((score, p))
    ranked.sort(key=lambda x: (x[0], -float(x[1]["price"])), reverse=True)
    results = [p for score, p in ranked if score > 0]
    db.search_events.insert_one({"query": q, "created_at": datetime.now(timezone.utc),
                                 "result_ids": [p["id"] for p in results]})
    return {"query": q, "results": results}

@app.get("/recommendations/{product_id}")
def recommendations(product_id: int):
    products = get_products()
    selected = next((p for p in products if p["id"] == product_id), None)
    if not selected:
        raise HTTPException(404, "Product not found")
    recs = [p for p in products if p["id"] != product_id]
    same_category = [p for p in recs if p["category"] == selected["category"]]
    result = (same_category + [p for p in recs if p not in same_category])[:3]
    db.recommendation_events.insert_one({"product_id": product_id,
        "recommended_ids": [p["id"] for p in result], "created_at": datetime.now(timezone.utc)})
    return {"for_product": selected["name"], "recommendations": result}

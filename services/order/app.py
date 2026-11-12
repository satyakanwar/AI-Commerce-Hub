import os, json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://commerce:commerce_dev_password@localhost:5432/commerce")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="Commerce Order Service")

@app.on_event("startup")
def startup():
    with engine.begin() as conn:
        conn.execute(text("""CREATE TABLE IF NOT EXISTS orders (
          id SERIAL PRIMARY KEY, customer_name VARCHAR(160) NOT NULL,
          items_json TEXT NOT NULL, total NUMERIC(10,2) NOT NULL,
          status VARCHAR(40) NOT NULL DEFAULT 'PLACED'
        )"""))

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "service": "order-service", "database": "postgresql"}

class Item(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=20)

class OrderIn(BaseModel):
    customer_name: str = Field(min_length=1, max_length=160)
    items: list[Item]

@app.post("/orders")
def create_order(order: OrderIn):
    if not order.items:
        raise HTTPException(400, "Order must contain at least one item")
    total = 0.0
    details = []
    for item in order.items:
        try:
            response = httpx.get(f"{PRODUCT_SERVICE_URL}/products/{item.product_id}", timeout=5)
            response.raise_for_status()
            product = response.json()
        except Exception:
            raise HTTPException(400, f"Product {item.product_id} is unavailable")
        subtotal = float(product["price"]) * item.quantity
        total += subtotal
        details.append({"product_id": item.product_id, "name": product["name"],
                        "quantity": item.quantity, "unit_price": float(product["price"]),
                        "subtotal": subtotal})
    with engine.begin() as conn:
        result = conn.execute(text("""INSERT INTO orders(customer_name,items_json,total)
          VALUES(:customer,:items,:total) RETURNING id"""),
          {"customer": order.customer_name, "items": json.dumps(details), "total": total})
        order_id = result.scalar()
    return {"order_id": order_id, "customer_name": order.customer_name,
            "items": details, "total": round(total, 2), "status": "PLACED"}

@app.get("/orders")
def list_orders():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id,customer_name,items_json,total,status FROM orders ORDER BY id DESC")).mappings().all()
    return [{"id": r["id"], "customer_name": r["customer_name"],
             "items": json.loads(r["items_json"]), "total": float(r["total"]),
             "status": r["status"]} for r in rows]

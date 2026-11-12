import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://commerce:commerce_dev_password@localhost:5432/commerce")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="Commerce Product Service")

SEED = [
    (1, "Nova X Smartphone", "Electronics", 24999, "6.5 inch display, 128GB storage, excellent camera"),
    (2, "AeroBook 14 Laptop", "Electronics", 57999, "14 inch laptop, 16GB RAM, 512GB SSD"),
    (3, "Pulse Wireless Headphones", "Electronics", 2999, "Wireless headphones with noise reduction"),
    (4, "Everyday Running Shoes", "Fashion", 1899, "Lightweight comfortable sports shoes"),
    (5, "Smart Fitness Watch", "Electronics", 4499, "Fitness tracking, heart rate and sleep insights"),
    (6, "Cotton Casual Shirt", "Fashion", 999, "Breathable cotton casual shirt")
]

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY, name VARCHAR(160) NOT NULL, category VARCHAR(80),
          price NUMERIC(10,2) NOT NULL, description TEXT
        )
        """))
        count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        if count == 0:
            for p in SEED:
                conn.execute(text("""INSERT INTO products(id,name,category,price,description)
                  VALUES(:id,:name,:category,:price,:description)"""),
                  dict(id=p[0], name=p[1], category=p[2], price=p[3], description=p[4]))

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "service": "product-service", "database": "postgresql"}

@app.get("/products")
def products():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id,name,category,price,description FROM products ORDER BY id")).mappings().all()
    return [dict(r) for r in rows]

@app.get("/products/{product_id}")
def product(product_id: int):
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id,name,category,price,description FROM products WHERE id=:id"),
                           {"id": product_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Product not found")
    return dict(row)

class ProductIn(BaseModel):
    name: str
    category: str
    price: float
    description: str = ""

@app.post("/products")
def create_product(p: ProductIn):
    with engine.begin() as conn:
        new_id = conn.execute(text("SELECT COALESCE(MAX(id),0)+1 FROM products")).scalar()
        conn.execute(text("""INSERT INTO products(id,name,category,price,description)
          VALUES(:id,:name,:category,:price,:description)"""),
          {"id": new_id, **p.model_dump()})
    return {"id": new_id, **p.model_dump()}

from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import (
    SQLModel,
    Field,
    Session,
    create_engine,
    select,
)

# ---------- Configuración de DB ----------

DATABASE_URL = "sqlite:///./prices.db"
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


# ---------- Modelos ----------

class ProductBase(SQLModel):
    name: str
    category: str
    cost: float
    price: float


class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    category: Optional[str] = None
    cost: Optional[float] = None
    price: Optional[float] = None


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    margin: float


class PriceHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    old_price: float
    new_price: float
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PriceHistoryRead(SQLModel):
    id: int
    product_id: int
    old_price: float
    new_price: float
    reason: Optional[str]
    created_at: datetime


class BulkIncreaseRequest(SQLModel):
    percentage: float
    category: Optional[str] = None
    reason: Optional[str] = "Ajuste masivo"


# ---------- FastAPI app ----------

app = FastAPI(
    title="Gestor de precios",
    description="API REST para gestionar productos, precios y aumentos masivos.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ---------- Helpers ----------

def compute_margin(cost: float, price: float) -> float:
    if cost == 0:
        return 0.0
    return round(((price - cost) / cost) * 100, 2)


def product_to_read(product: Product) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        category=product.category,
        cost=product.cost,
        price=product.price,
        created_at=product.created_at,
        updated_at=product.updated_at,
        margin=compute_margin(product.cost, product.price),
    )


# ---------- Endpoints de productos ----------

@app.post("/products", response_model=ProductRead, tags=["Productos"])
def create_product(
    data: ProductCreate,
    session: Session = Depends(get_session),
):
    product = Product.from_orm(data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product_to_read(product)


@app.get("/products", response_model=List[ProductRead], tags=["Productos"])
def list_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    return [product_to_read(p) for p in products]


@app.get(
    "/products/{product_id}",
    response_model=ProductRead,
    tags=["Productos"],
)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product_to_read(product)


@app.put(
    "/products/{product_id}",
    response_model=ProductRead,
    tags=["Productos"],
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    old_price = product.price

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    product.updated_at = datetime.utcnow()
    session.add(product)

    # si cambió el precio, guardar historial
    if "price" in update_data and update_data["price"] != old_price:
        history = PriceHistory(
            product_id=product.id,
            old_price=old_price,
            new_price=product.price,
            reason="Actualización individual",
        )
        session.add(history)

    session.commit()
    session.refresh(product)
    return product_to_read(product)


@app.delete("/products/{product_id}", tags=["Productos"])
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    session.delete(product)
    session.commit()
    return {"detail": "Producto eliminado"}


# ---------- Aumentos masivos ----------

@app.post(
    "/products/increase",
    tags=["Aumentos"],
    summary="Aumentar precios masivamente",
)
def bulk_increase(
    payload: BulkIncreaseRequest,
    session: Session = Depends(get_session),
):
    query = select(Product)
    if payload.category:
        query = query.where(Product.category == payload.category)

    products = session.exec(query).all()
    if not products:
        return {"updated": 0}

    factor = 1 + payload.percentage / 100.0
    updated_count = 0

    for product in products:
        old_price = product.price
        new_price = round(old_price * factor, 2)

        product.price = new_price
        product.updated_at = datetime.utcnow()
        session.add(product)

        history = PriceHistory(
            product_id=product.id,
            old_price=old_price,
            new_price=new_price,
            reason=payload.reason,
        )
        session.add(history)

        updated_count += 1

    session.commit()
    return {
        "updated": updated_count,
        "percentage": payload.percentage,
        "category": payload.category,
    }


# ---------- Historial ----------

@app.get(
    "/products/{product_id}/history",
    response_model=List[PriceHistoryRead],
    tags=["Historial"],
)
def get_history(
    product_id: int,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    history = session.exec(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.created_at.desc())
    ).all()

    return history


from fastapi import APIRouter, HTTPException
from loguru import logger

from sqlmodel import select
from typing import List


from app.models import Product, User, Item, ProductCreate, ProductUpdate
from app.api.deps import SessionDep, CurrentUser, RedisDep, custom_serializer

router = APIRouter(tags=["products"], prefix="/products")

import json  # Add this import at the top of your file


@router.post("/", response_model=Product)
def create_product(
        *,
        session: SessionDep,
        product_in: ProductCreate
) -> Product:
    """
    Creates a new product.
    """
    curr_product = session.exec(select(Product).filter_by(name=product_in.name)).first()
    if curr_product:
        raise HTTPException(
            status_code=400,
            detail=f"Product {product_in.name} already exists"
        )
    product = Product.model_validate(product_in)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.patch("/update", response_model=Product)
def update_product(
        *,
        session: SessionDep,
        product_name: str,
        product_in: ProductUpdate
) -> Product:
    """
    Updates price and rating of the chosen product by its name.
    """
    product = session.exec(select(Product).where(Product.name == product_name)).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with name {product_name} not found"
        )

    if product_in.price is not None:
        product.price = product_in.price
    if product_in.rating is not None:
        product.rating = product_in.rating

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/delete", response_model=dict)
def delete_product(
        *,
        session: SessionDep,
        product_name: str
) -> dict:
    """
    Deletes a product by its name.
    """
    product = session.exec(select(Product).where(Product.name == product_name)).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with name {product_name} not found"
        )

    session.delete(product)
    session.commit()
    return {"message": f"Product {product_name} deleted successfully"}


@router.get("/read/{product_name}", response_model=Product)
def read_product(
        *,
        session: SessionDep,
        product_name: str
) -> Product:
    """
    Retrieves a product by its name.
    """
    product = session.exec(select(Product).where(Product.name == product_name)).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with name {product_name} not found"
        )
    return product

@router.get("/recommendations", response_model=List[Product])
def get_recommendations(
        number_of_products: int,
        user: CurrentUser,
        session: SessionDep,
        redis_client: RedisDep,
):
    """
    Returns a list of recommended products depending on user's preferences
    """
    cache_key = f"recommendations: {str(user.id)}"
    try:

        cached_result = redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
    except Exception as re:
        logger.error(f"Redis error: {re}")
        raise HTTPException(
            status_code=500,
            detail="Probably our server decided not to answer you. Please do not blame it,"
                   "blame the programmer who developed it)"
        )

    user = session.exec(select(User).where(User.id == user.id)).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    purchased_items = session.exec(select(Item).where(Item.owner_id == user.id)).all()
    if not purchased_items:
        raise  HTTPException(status_code=404,
                             detail="You have no recommendations, start buying to get them!")
    purchased_categories = {item.category for item in purchased_items}

    recommended_products = session.exec(
        select(Product)
        .where(Product.category.in_(purchased_categories))
        .order_by(Product.rating.desc())
        .limit(number_of_products)
    ).all()
    serialized_products = json.dumps([product.dict() for product in recommended_products], default=custom_serializer)
    redis_client.set(cache_key, serialized_products, ex=100)
    return recommended_products

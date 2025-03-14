import json
import logging
from typing import List, Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine, init_db
from app.models import ProductCreate, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def create_products(
        *,
        session: Session,
        products_in: List[ProductCreate]
) -> Any:
    """
    Creates multiple products.
    """
    products = []
    for product_data in products_in:
        product = Product.model_validate(product_data)
        session.add(product)
        products.append(product)
    session.commit()
    for product in products:
        session.refresh(product)

def init_test_data():
    """
    Adds test products to the db, if INIT_DB == True
    """
    if settings.INIT_DB:
        try:
            with Session(engine) as sess:
                add_products_to_db(session=sess)
                sess.commit()
        except IntegrityError as ie:
            logger.error(f"Error initializing test products: {ie}")


def add_products_to_db(session: Session):
    with open(settings.PRODUCTS_JSON, 'r', encoding='utf-8') as file:
        products_data = json.load(file)
    create_products(session=session, products_in=products_data)




def main() -> None:
    logger.info("Creating initial data")
    init_test_data()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()

from unittest.mock import patch, Mock

from fastapi.testclient import TestClient


from app.core.config import settings
from app.models import Product





@patch("app.api.deps.SessionDep", new_callable=Mock)
def test_get_all_products_not_found(mock_session, client: TestClient):
    mock_session.exec.return_value.all.return_value = []
    response = client.get("api/v1/products/all")
    assert response.status_code == 200

def test_delete_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Сначала создаем продукт
    create_data = {
        "name": "product_to_delete",
        "category": "Outdoor",
        "price": 100.0,
        "rating": 4.7,
    }
    create_response = client.post(
        f"{settings.API_V1_STR}/products/",
        headers=superuser_token_headers,
        json=create_data,
    )
    assert create_response.status_code == 200

    # Удаляем продукт
    delete_response = client.delete(
        f"{settings.API_V1_STR}/products/delete?product_name=product_to_delete",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 200
    content = delete_response.json()
    assert content["message"] == "Product product_to_delete deleted successfully"

    # Проверяем, что продукт действительно удален
    read_response = client.get(
        f"{settings.API_V1_STR}/products/product_to_delete",
        headers=superuser_token_headers,
    )
    assert read_response.status_code == 404

def test_delete_product_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    delete_response = client.delete(
        f"{settings.API_V1_STR}/products/delete?product_name=nonexistent_product",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 404
    content = delete_response.json()
    assert content["detail"] == "Product with name nonexistent_product not found"


def test_read_product_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    read_response = client.get(
        f"{settings.API_V1_STR}/products/read/nonexistent_product",
        headers=superuser_token_headers,
    )
    assert read_response.status_code == 404
    content = read_response.json()
    assert content["detail"] == "Product with name nonexistent_product not found"
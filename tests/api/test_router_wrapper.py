from fastapi import FastAPI
from fastapi.testclient import TestClient

from regtech_api_commons.api.router_wrapper import Router

router = Router()


@router.api_route("/items/{item_id}", methods=["GET"])
def get_items(item_id: str):
    return {"item_id": item_id}


def get_not_decorated(item_id: str):
    return {"item_id": item_id}


router.add_api_route("/items-not-decorated/{item_id}", get_not_decorated)

app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_get_api_route():
    response = client.get("/items/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}


def test_get_api_route_ends_with_forward_slash():
    response = client.get("/items/foo/")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}


def test_get_api_route_wrong_path():
    response = client.get("/item/foo/")
    assert response.status_code != 200, response.text
    assert response.json() != {"item_id": "foo"}


def test_get_api_route_not_decorated():
    response = client.get("/items-not-decorated/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}
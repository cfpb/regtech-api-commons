from fastapi import FastAPI
from fastapi.testclient import TestClient
from regtech_api_commons.api.router_wrapper import Router

router = Router()
app = FastAPI()


@router.api_route("/items/{item_id}", methods=["GET"])
def get_items(item_id: str):
    return {"item_id": item_id}


app.include_router(router)

client = TestClient(app)


def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200, response.text
    assert response.json() == "Service is up."


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
    assert response.status_code == 404, response.text
    assert response.json() != {"item_id": "foo"}

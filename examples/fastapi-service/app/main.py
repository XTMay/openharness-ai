from fastapi import FastAPI

app = FastAPI(title="OpenHarness Example API")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/products")
def list_products() -> list[dict[str, str]]:
    return [{"id": "sku-1", "name": "Example product"}]


@app.post("/orders")
def create_order() -> dict[str, str]:
    return {"id": "order-1", "status": "created"}


@app.post("/checkout")
def checkout() -> dict[str, str]:
    return {"id": "checkout-1", "status": "accepted"}


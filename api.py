# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import Union


# class Item(BaseModel):
#   name: str
#   description: str | None = None
#   price: float
#   tax: float | None = None

# class ItemList(BaseModel):
#   items: list[Item]


# app = FastAPI()

# @app.get("/items")
# def get_all_items():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
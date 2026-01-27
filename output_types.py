from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from typing import Dict, Literal, Optional
from enum import Enum

MUnit = Literal["kg", "g", "l", "ml", "u"]
Status = Literal["success", "failure"]

class BItem(BaseModel):
    name: str = Field(..., description="Name of the item in the bill.")
    measureUnit: Optional[MUnit] = Field(..., description="Measure unit of the item in the bill.")
    unitPrice: float = Field(..., description="Price per unit of measurement per item in the bill.")
    quantity: int = Field(..., description="Quantity of the item in the bill, measured in its measure unit.")
    
class BillItems(BaseModel):
    message: Status = Field(..., description="Message from the LLM indicating the success or failure of the extraction.")
    bitems: list[BItem] = Field([], description="List of items in the bill, with their name, unitary price and quantity.")

class ItemSuggestions(BaseModel):
    found: bool = Field(..., description="Indicates if any similar items were found in the database.")
    suggestions: Optional[Dict[str, BItem]] = Field(default={}, description="Dictionary mapping item names from the bill to suggested items from the database.")

class State(TypedDict):
    billItems: BillItems
    dbItems: list[str]
    itemPairs: ItemSuggestions
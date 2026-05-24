from decimal import Decimal

from pydantic import BaseModel


class CartItem(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: Decimal


class ShoppingCart(BaseModel):
    cart_id: int
    customer_name: str
    items: list[CartItem]

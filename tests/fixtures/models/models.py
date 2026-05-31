from decimal import Decimal

from pydantic import BaseModel


class CartItem(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: Decimal
    discount: Decimal = Decimal("0.00")


class ShoppingCart(BaseModel):
    cart_id: int
    customer_name: str
    items: list[CartItem]
    notes: str | None = None


class NotAModel:
    pass

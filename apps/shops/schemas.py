from typing import Optional
from ninja import Field, Schema
from pydantic import EmailStr


class ShopCreateSchema(Schema):
    name: str = Field(..., examples=["My shop"], description="Name of the shop")
    description: Optional[str] = Field(
        None, examples=["This is my shop"], description="Description of the shop"
    )
    email: Optional[EmailStr] = Field(
        None, examples=["shop@example.com"], description="Contact email of the shop"
    )

    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

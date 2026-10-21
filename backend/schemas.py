
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field



class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    venue: str = Field(min_length=1, max_length=200)
    starts_at: datetime
    rows: dict[str, int] = Field(
        description="Number of seats per row, e.g. {'A': 10, 'B': 12}"
    )
    row_prices: dict[str, float] = Field(
        description="Ticket price for each row, e.g. {'A': 200, 'B': 150}"
    )


class EventResponse(BaseModel):
    id: int
    name: str
    description: str | None
    venue: str
    starts_at: datetime
    total_seats: int

    model_config = ConfigDict(from_attributes=True)

class SeatResponse(BaseModel):
    id: int
    event_id: int
    row_label: str
    seat_number: int
    price: float
    status: str

    model_config = ConfigDict(from_attributes=True)


from pydantic import EmailStr


class SeatHoldRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=150)
    customer_email: EmailStr
    seat_ids: list[int] = Field(min_length=1)


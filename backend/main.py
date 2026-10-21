
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import secrets
import qrcode
import base64
from io import BytesIO

import models
import schemas
from database import Base, engine, get_db


app = FastAPI(
    title="Housefull API",
    description="Seat booking and event management API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_qr_code(ticket_code: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket_code)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded_image}"


# Create missing database tables during startup.
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Welcome to Housefull!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# EVENTS
# --------------------------------------------------

@app.post(
    "/events",
    response_model=schemas.EventResponse,
    status_code=201,
)
def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
):
    if not event.rows:
        raise HTTPException(
            status_code=400,
            detail="At least one row is required",
        )

    if set(event.rows.keys()) != set(event.row_prices.keys()):
        raise HTTPException(
            status_code=400,
            detail="Every seat row must have exactly one row price",
        )

    if any(count < 1 for count in event.rows.values()):
        raise HTTPException(
            status_code=400,
            detail="Each row must contain at least one seat",
        )

    if any(price < 0 for price in event.row_prices.values()):
        raise HTTPException(
            status_code=400,
            detail="Ticket prices cannot be negative",
        )

    total_seats = sum(event.rows.values())

    new_event = models.Event(
        name=event.name,
        description=event.description,
        venue=event.venue,
        starts_at=event.starts_at,
        total_seats=total_seats,
    )

    try:
        db.add(new_event)
        db.flush()

        for row_label, seat_count in event.rows.items():
            for seat_number in range(1, seat_count + 1):
                seat = models.Seat(
                    event_id=new_event.id,
                    row_label=row_label,
                    seat_number=seat_number,
                    price=event.row_prices[row_label],
                    status="available",
                )
                db.add(seat)

        db.commit()
        db.refresh(new_event)
        return new_event

    except Exception:
        db.rollback()
        raise


@app.get(
    "/events",
    response_model=list[schemas.EventResponse],
)
def get_events(db: Session = Depends(get_db)):
    return (
        db.query(models.Event)
        .order_by(models.Event.id.desc())
        .all()
    )


@app.get(
    "/events/{event_id}",
    response_model=schemas.EventResponse,
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = (
        db.query(models.Event)
        .filter(models.Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return event


@app.get(
    "/events/{event_id}/seats",
    response_model=list[schemas.SeatResponse],
)
def get_event_seats(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = (
        db.query(models.Event)
        .filter(models.Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return (
        db.query(models.Seat)
        .filter(models.Seat.event_id == event_id)
        .order_by(
            models.Seat.row_label,
            models.Seat.seat_number,
        )
        .all()
    )


# --------------------------------------------------
# SEAT HOLDING AND BOOKING
# --------------------------------------------------

@app.post("/bookings/hold", status_code=201)
def hold_seats(
    request: schemas.SeatHoldRequest,
    db: Session = Depends(get_db),
):
    seat_ids = request.seat_ids

    if not seat_ids:
        raise HTTPException(
            status_code=400,
            detail="Select at least one seat",
        )

    if len(seat_ids) != len(set(seat_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate seat IDs are not allowed",
        )

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)

    try:
        seats = db.scalars(
            select(models.Seat)
            .where(models.Seat.id.in_(seat_ids))
            .order_by(models.Seat.id)
            .with_for_update()
        ).all()

        if len(seats) != len(seat_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more seats were not found",
            )

        # All selected seats must belong to one event.
        if any(
            seat.event_id != seats[0].event_id
            for seat in seats
        ):
            raise HTTPException(
                status_code=400,
                detail="All seats must belong to the same event",
            )

        # Release expired holds.
        for seat in seats:
            if (
                seat.status == "held"
                and seat.hold_expires_at is not None
                and seat.hold_expires_at <= now
            ):
                seat.status = "available"
                seat.hold_expires_at = None

        unavailable = [
            seat.id
            for seat in seats
            if seat.status != "available"
        ]

        if unavailable:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Some seats are not available",
                    "seat_ids": unavailable,
                },
            )

        total_amount = sum(
            float(seat.price) for seat in seats
        )

        booking = models.Booking(
            booking_code=secrets.token_urlsafe(12),
            event_id=seats[0].event_id,
            customer_name=request.customer_name,
            customer_email=str(request.customer_email),
            status="pending",
            total_amount=total_amount,
            expires_at=expires_at,
        )

        db.add(booking)
        db.flush()

        for seat in seats:
            seat.status = "held"
            seat.hold_expires_at = expires_at

            db.add(
                models.BookingSeat(
                    booking_id=booking.id,
                    seat_id=seat.id,
                    price_at_booking=seat.price,
                )
            )

        db.commit()
        db.refresh(booking)

        return {
            "message": "Seats held successfully",
            "booking_code": booking.booking_code,
            "event_id": booking.event_id,
            "seat_ids": seat_ids,
            "total_amount": total_amount,
            "status": booking.status,
            "expires_at": expires_at.isoformat(),
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# MOCK PAYMENT
# --------------------------------------------------

class PaymentRequest(BaseModel):
    booking_code: str
    payment_status: str


@app.post("/payments/mock")
def mock_payment(
    request: PaymentRequest,
    db: Session = Depends(get_db),
):
    try:
        booking = (
            db.query(models.Booking)
            .filter(
                models.Booking.booking_code == request.booking_code
            )
            .with_for_update()
            .first()
        )

        if booking is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        if booking.status != "pending":
            raise HTTPException(
                status_code=409,
                detail=f"Booking is already {booking.status}",
            )

        now = datetime.now(timezone.utc)

        if (
            booking.expires_at is None
            or booking.expires_at <= now
        ):
            booking.status = "expired"

            seats = (
                db.query(models.Seat)
                .join(
                    models.BookingSeat,
                    models.BookingSeat.seat_id == models.Seat.id,
                )
                .filter(
                    models.BookingSeat.booking_id == booking.id
                )
                .all()
            )

            for seat in seats:
                if seat.status == "held":
                    seat.status = "available"
                    seat.hold_expires_at = None

            db.commit()

            raise HTTPException(
                status_code=409,
                detail="Seat hold has expired",
            )

        if request.payment_status not in ("success", "fail"):
            raise HTTPException(
                status_code=400,
                detail="payment_status must be 'success' or 'fail'",
            )

        seats = (
            db.query(models.Seat)
            .join(
                models.BookingSeat,
                models.BookingSeat.seat_id == models.Seat.id,
            )
            .filter(
                models.BookingSeat.booking_id == booking.id
            )
            .with_for_update()
            .all()
        )

        if request.payment_status == "fail":
            booking.status = "failed"

            for seat in seats:
                if seat.status == "held":
                    seat.status = "available"
                    seat.hold_expires_at = None

            db.commit()

            return {
                "message": "Payment failed; held seats have been released",
                "booking_code": booking.booking_code,
                "status": booking.status,
            }

        for seat in seats:
            if seat.status != "held":
                raise HTTPException(
                    status_code=409,
                    detail=f"Seat {seat.id} is no longer held",
                )

        booking.status = "confirmed"

        for seat in seats:
            seat.status = "booked"
            seat.hold_expires_at = None

        ticket = models.Ticket(
            booking_id=booking.id,
            ticket_code=secrets.token_urlsafe(16),
        )

        db.add(ticket)
        db.commit()

        return {
            "message": "Payment successful",
            "booking_code": booking.booking_code,
            "status": booking.status,
            "ticket_code": ticket.ticket_code,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# TICKET RETRIEVAL AND QR CODE
# --------------------------------------------------

@app.get("/tickets/{booking_code}")
def get_ticket(
    booking_code: str,
    db: Session = Depends(get_db),
):
    booking = (
        db.query(models.Booking)
        .filter(
            models.Booking.booking_code == booking_code
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=409,
            detail="Ticket is available only for confirmed bookings",
        )

    ticket = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.booking_id == booking.id
        )
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    booking_seats = (
        db.query(models.BookingSeat, models.Seat)
        .join(
            models.Seat,
            models.BookingSeat.seat_id == models.Seat.id,
        )
        .filter(
            models.BookingSeat.booking_id == booking.id
        )
        .order_by(
            models.Seat.row_label,
            models.Seat.seat_number,
        )
        .all()
    )

    return {
        "booking_code": booking.booking_code,
        "customer_name": booking.customer_name,
        "customer_email": booking.customer_email,
        "event_id": booking.event_id,
        "status": booking.status,
        "total_amount": float(booking.total_amount),
        "ticket_code": ticket.ticket_code,
        "qr_code": generate_qr_code(ticket.ticket_code),
        "seats": [
            {
                "row": seat.row_label,
                "seat_number": seat.seat_number,
                "price": float(booking_seat.price_at_booking),
            }
            for booking_seat, seat in booking_seats
        ],
    }


# --------------------------------------------------
# STAFF CHECK-IN
# --------------------------------------------------

@app.post("/check-in/{ticket_code}")
def check_in_ticket(
    ticket_code: str,
    db: Session = Depends(get_db),
):
    try:
        ticket = (
            db.query(models.Ticket)
            .filter(
                models.Ticket.ticket_code == ticket_code
            )
            .with_for_update()
            .first()
        )

        if ticket is None:
            raise HTTPException(
                status_code=404,
                detail="Ticket not found",
            )

        if ticket.checked_in_at is not None:
            raise HTTPException(
                status_code=409,
                detail="This ticket has already been checked in",
            )

        booking = (
            db.query(models.Booking)
            .filter(
                models.Booking.id == ticket.booking_id
            )
            .first()
        )

        if booking is None or booking.status != "confirmed":
            raise HTTPException(
                status_code=409,
                detail="Only confirmed bookings can check in",
            )

        booking_seats = (
            db.query(models.BookingSeat, models.Seat)
            .join(
                models.Seat,
                models.BookingSeat.seat_id == models.Seat.id,
            )
            .filter(
                models.BookingSeat.booking_id == booking.id
            )
            .order_by(
                models.Seat.row_label,
                models.Seat.seat_number,
            )
            .all()
        )

        seat_numbers = [
            f"{seat.row_label}{seat.seat_number}"
            for booking_seat, seat in booking_seats
        ]

        ticket.checked_in_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "message": "Check-in successful",
            "ticket_code": ticket.ticket_code,
            "customer_name": booking.customer_name,
            "seat_numbers": seat_numbers,
            "checked_in_at": ticket.checked_in_at.isoformat(),
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# ORGANISER DASHBOARD
# --------------------------------------------------

@app.get("/events/{event_id}/dashboard")
def get_event_dashboard(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = (
        db.query(models.Event)
        .filter(models.Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    seats = (
        db.query(models.Seat)
        .filter(models.Seat.event_id == event_id)
        .all()
    )

    total_seats = len(seats)
    available_seats = sum(
        1 for seat in seats if seat.status == "available"
    )
    held_seats = sum(
        1 for seat in seats if seat.status == "held"
    )
    booked_seats = sum(
        1 for seat in seats if seat.status == "booked"
    )

    confirmed_bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.event_id == event_id,
            models.Booking.status == "confirmed",
        )
        .all()
    )

    total_revenue = sum(
        float(booking.total_amount)
        for booking in confirmed_bookings
    )

    checked_in_count = (
        db.query(models.Ticket)
        .join(
            models.Booking,
            models.Booking.id == models.Ticket.booking_id,
        )
        .filter(
            models.Booking.event_id == event_id,
            models.Booking.status == "confirmed",
            models.Ticket.checked_in_at.isnot(None),
        )
        .count()
    )

    return {
        "event_id": event.id,
        "event_name": event.name,
        "total_seats": total_seats,
        "available_seats": available_seats,
        "held_seats": held_seats,
        "booked_seats": booked_seats,
        "confirmed_bookings": len(confirmed_bookings),
        "total_revenue": round(total_revenue, 2),
        "checked_in_count": checked_in_count,
    }


# --------------------------------------------------
# BOOKING CANCELLATION
# --------------------------------------------------

@app.post("/bookings/{booking_code}/cancel")
def cancel_booking(
    booking_code: str,
    db: Session = Depends(get_db),
):
    try:
        booking = (
            db.query(models.Booking)
            .filter(
                models.Booking.booking_code == booking_code
            )
            .with_for_update()
            .first()
        )

        if booking is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        if booking.status != "confirmed":
            raise HTTPException(
                status_code=409,
                detail="Only confirmed bookings can be cancelled",
            )

        booking_seats = (
            db.query(models.BookingSeat)
            .filter(
                models.BookingSeat.booking_id == booking.id
            )
            .all()
        )

        for booking_seat in booking_seats:
            seat = (
                db.query(models.Seat)
                .filter(
                    models.Seat.id == booking_seat.seat_id
                )
                .with_for_update()
                .first()
            )

            if seat is not None:
                seat.status = "available"
                seat.hold_expires_at = None

        booking.status = "cancelled"
        db.commit()

        return {
            "message": "Booking cancelled successfully",
            "booking_code": booking.booking_code,
            "status": booking.status,
            "released_seats": len(booking_seats),
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not cancel booking",
        )

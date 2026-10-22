
import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Use a separate temporary SQLite database for tests.
# This keeps tests isolated from the real PostgreSQL database.
test_db_path = (
    Path(tempfile.gettempdir())
    / f"housefull_test_{uuid.uuid4().hex}.db"
)

os.environ["DATABASE_URL"] = (
    f"sqlite:///{test_db_path.as_posix()}"
)

import main


@pytest.fixture(autouse=True)
def reset_test_database():
    main.Base.metadata.drop_all(bind=main.engine)
    main.Base.metadata.create_all(bind=main.engine)

    yield

    main.Base.metadata.drop_all(bind=main.engine)


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers():
    token = main.create_access_token(main.ADMIN_USERNAME)

    return {
        "Authorization": f"Bearer {token}"
    }


# --------------------------------------------------
# TEST HELPERS
# --------------------------------------------------

def create_test_event(client, admin_headers):
    response = client.post(
        "/events",
        headers=admin_headers,
        json={
            "name": "Housefull Test Event",
            "description": "Test event",
            "venue": "Bangalore",
            "starts_at": "2026-12-25T18:00:00+05:30",
            "rows": {
                "A": 3,
                "B": 3,
            },
            "row_prices": {
                "A": 200,
                "B": 150,
            },
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def hold_seats(client, event_id, seat_ids):
    response = client.post(
        "/bookings/hold",
        json={
            "customer_name": "Rohit",
            "customer_email": "rohit@example.com",
            "seat_ids": seat_ids,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def make_confirmed_booking(client, event_id, seat_ids):
    booking = hold_seats(
        client,
        event_id,
        seat_ids,
    )

    payment_response = client.post(
        "/payments/mock",
        json={
            "booking_code": booking["booking_code"],
            "payment_status": "success",
        },
    )

    assert payment_response.status_code == 200, (
        payment_response.text
    )

    return booking, payment_response.json()


# --------------------------------------------------
# TEST 1: EVENT CREATION AND SEAT HOLD
# --------------------------------------------------

def test_event_creation_and_seat_hold(
    client,
    admin_headers,
):
    event = create_test_event(client, admin_headers)

    assert event["name"] == "Housefull Test Event"
    assert event["total_seats"] == 6

    seats_response = client.get(
        f"/events/{event['id']}/seats"
    )

    assert seats_response.status_code == 200

    seats = seats_response.json()

    assert len(seats) == 6

    booking = hold_seats(
        client,
        event["id"],
        [seats[0]["id"]],
    )

    assert booking["status"] == "pending"
    assert booking["total_amount"] == 200.0

    updated_seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    held_seat = next(
        seat for seat in updated_seats
        if seat["id"] == seats[0]["id"]
    )

    assert held_seat["status"] == "held"


# --------------------------------------------------
# TEST 2: FAILED PAYMENT RELEASES SEATS
# --------------------------------------------------

def test_failed_payment_releases_seats(
    client,
    admin_headers,
):
    event = create_test_event(client, admin_headers)

    seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    selected_seat_id = seats[0]["id"]

    booking = hold_seats(
        client,
        event["id"],
        [selected_seat_id],
    )

    payment_response = client.post(
        "/payments/mock",
        json={
            "booking_code": booking["booking_code"],
            "payment_status": "fail",
        },
    )

    assert payment_response.status_code == 200

    result = payment_response.json()

    assert result["status"] == "failed"

    updated_seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    released_seat = next(
        seat for seat in updated_seats
        if seat["id"] == selected_seat_id
    )

    assert released_seat["status"] == "available"


# --------------------------------------------------
# TEST 3: SUCCESSFUL PAYMENT, TICKET AND CHECK-IN
# --------------------------------------------------

def test_successful_payment_ticket_and_checkin(
    client,
    admin_headers,
):
    event = create_test_event(client, admin_headers)

    seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    booking, payment_result = make_confirmed_booking(
        client,
        event["id"],
        [seats[0]["id"]],
    )

    assert payment_result["status"] == "confirmed"

    ticket_response = client.get(
        f"/tickets/{booking['booking_code']}"
    )

    assert ticket_response.status_code == 200

    ticket = ticket_response.json()

    assert ticket["booking_code"] == booking["booking_code"]
    assert ticket["customer_name"] == "Rohit"
    assert ticket["ticket_code"]
    assert ticket["qr_code"].startswith("data:image/png;base64,")
    assert len(ticket["seats"]) == 1

    checkin_response = client.post(
        f"/check-in/{ticket['ticket_code']}"
    )

    assert checkin_response.status_code == 200
    assert checkin_response.json()["customer_name"] == "Rohit"

    # A ticket must not be admitted twice.
    duplicate_checkin = client.post(
        f"/check-in/{ticket['ticket_code']}"
    )

    assert duplicate_checkin.status_code == 409


# --------------------------------------------------
# TEST 4: SAME SEAT CANNOT BE BOOKED TWICE
# --------------------------------------------------

def test_same_seat_cannot_be_booked_twice(
    client,
    admin_headers,
):
    event = create_test_event(client, admin_headers)

    seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    selected_seat_id = seats[0]["id"]

    first_booking = hold_seats(
        client,
        event["id"],
        [selected_seat_id],
    )

    assert first_booking["status"] == "pending"

    second_response = client.post(
        "/bookings/hold",
        json={
            "customer_name": "Another Customer",
            "customer_email": "another@example.com",
            "seat_ids": [selected_seat_id],
        },
    )

    assert second_response.status_code == 409


# --------------------------------------------------
# TEST 5: EVENT CREATION REQUIRES ADMIN LOGIN
# --------------------------------------------------

def test_event_creation_requires_admin_login(client):
    response = client.post(
        "/events",
        json={
            "name": "Unauthorized Event",
            "description": "This should not be created",
            "venue": "Bangalore",
            "starts_at": "2026-12-25T18:00:00+05:30",
            "rows": {
                "A": 3,
            },
            "row_prices": {
                "A": 200,
            },
        },
    )

    assert response.status_code == 401


# --------------------------------------------------
# TEST 6: CONFIRMED BOOKING CANNOT BE PAID TWICE
# --------------------------------------------------

def test_confirmed_booking_cannot_be_paid_twice(
    client,
    admin_headers,
):
    event = create_test_event(client, admin_headers)

    seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    booking, _ = make_confirmed_booking(
        client,
        event["id"],
        [seats[0]["id"]],
    )

    second_payment = client.post(
        "/payments/mock",
        json={
            "booking_code": booking["booking_code"],
            "payment_status": "success",
        },
    )

    assert second_payment.status_code == 409


# --------------------------------------------------
# TEST 7: CANCELLATION REQUIRES ADMIN AND RELEASES SEATS
# --------------------------------------------------

def test_cancelling_booking_releases_seats(
    client,
    admin_headers,
):
    event = create_test_event(client, admin_headers)

    seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    selected_seat_id = seats[0]["id"]

    booking, _ = make_confirmed_booking(
        client,
        event["id"],
        [selected_seat_id],
    )

    # An unauthenticated cancellation must be rejected.
    unauthorized_response = client.post(
        f"/bookings/{booking['booking_code']}/cancel"
    )

    assert unauthorized_response.status_code == 401

    # An authenticated admin can cancel the booking.
    cancel_response = client.post(
        f"/bookings/{booking['booking_code']}/cancel",
        headers=admin_headers,
    )

    assert cancel_response.status_code == 200, (
        cancel_response.text
    )

    result = cancel_response.json()

    assert result["status"] == "cancelled"
    assert result["booking_code"] == booking["booking_code"]
    assert result["released_seats"] == 1

    # Confirm the simulated refund was recorded in the response.
    refund = result["refund"]

    assert refund["reference"].startswith("MOCK-REFUND-")
    assert refund["status"] == "mock_refunded"
    assert refund["amount"] == booking["total_amount"]
    assert "no real money was transferred" in refund["note"]

    # Confirm the cancelled booking's seat is available again.
    updated_seats = client.get(
        f"/events/{event['id']}/seats"
    ).json()

    released_seat = next(
        seat for seat in updated_seats
        if seat["id"] == selected_seat_id
    )

    assert released_seat["status"] == "available"

    # A second cancellation must not succeed.
    second_cancel_response = client.post(
        f"/bookings/{booking['booking_code']}/cancel",
        headers=admin_headers,
    )

    assert second_cancel_response.status_code == 409

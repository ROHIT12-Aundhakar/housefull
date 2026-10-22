
# Housefull — Seat Booking System

Housefull is a full-stack event seat-booking application designed for comedy shows, college festivals, movies, and small venues. It helps organisers manage events, seats, bookings, payments, tickets, check-ins, and booking cancellations.

## Features

- **Event management:** Create events with venue, date, time, seat rows, and row-based pricing.
- **Seat booking:** View seat availability and temporarily hold seats for five minutes while completing payment.
- **Mock payments:** Simulate successful and failed payments.
- **Digital tickets:** Generate booking tickets with unique ticket codes and QR codes.
- **Door check-in:** Validate tickets and prevent duplicate check-ins.
- **Organiser dashboard:** View seat statistics, booking history, revenue, ticket details, and check-in information.
- **Booking cancellation:** Allow authenticated organisers to cancel eligible bookings and release seats.
- **Mock refunds:** Record simulated refund details. No real money is transferred.
- **Admin authentication:** Protect organiser operations using token-based authentication.
- **Automated tests:** Test important booking, payment, ticket, cancellation, refund, and dashboard workflows.

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT-based authentication
- QR code generation
- Pytest

### Frontend
- React
- JavaScript
- CSS
- Vite

## Project Structure

```text
housefull/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── test_main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
├── .gitignore
└── README.md
```

## Prerequisites

Install the following before running the project:

- Python 3.11 or a compatible Python version
- Node.js and npm
- PostgreSQL
- Git

## Backend Setup

Open a terminal in the project directory and navigate to the backend:

```powershell
cd backend
```

Create and activate a virtual environment on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file inside the `backend` directory. Configure the database connection and required admin authentication settings.

The application requires these environment variables:

```text
DATABASE_URL
ADMIN_USERNAME
ADMIN_PASSWORD_HASH
JWT_SECRET_KEY
```

Use values appropriate for your local environment. Generate a secure password hash using the password-hashing library configured by the application, and use a strong, randomly generated JWT secret.

**Security:** Never commit `.env` files, database passwords, admin passwords, JWT secrets, or access tokens to GitHub.

### Start the Backend

From the `backend` directory, run:

```powershell
uvicorn main:app --reload
```

The backend should be available at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Frontend Setup

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in your terminal, commonly:

http://localhost:5173/

Keep the backend running while using the frontend.

## Running Automated Tests

Open a terminal in the backend directory and activate the virtual environment.

Run the test suite:

```powershell
python -m pytest -v
```

The tests use a separate temporary SQLite database to avoid modifying the configured PostgreSQL database.

The test suite covers event creation, seat holds, failed payments, successful payments, ticket generation, check-in, duplicate booking prevention, admin authentication, cancellation, refunds, and dashboard details.

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| POST | `/admin/login` | Authenticate an organiser |
| GET | `/admin/me` | Get the authenticated admin |
| POST | `/events` | Create an event |
| GET | `/events` | List events |
| GET | `/events/{event_id}` | Get event details |
| GET | `/events/{event_id}/seats` | Get seat availability |
| POST | `/bookings/hold` | Temporarily hold selected seats |
| POST | `/payments/mock` | Simulate a payment |
| GET | `/tickets/{booking_code}` | Retrieve ticket details |
| POST | `/check-in/{ticket_code}` | Validate and check in a ticket |
| GET | `/events/{event_id}/dashboard` | View organiser dashboard |
| POST | `/bookings/{booking_code}/cancel` | Cancel an eligible booking |

Some endpoints require admin authentication. Request and response schemas are available in the interactive API documentation at `/docs`.

## Booking Workflow

1. An organiser signs in and creates an event.
2. A customer views the event and selects available seats.
3. The selected seats are temporarily held for five minutes.
4. The customer completes a simulated payment.
5. Successful payment confirms the booking and generates a ticket with a QR code.
6. Staff validate the ticket at the venue using its ticket code.
7. An authorised organiser can cancel an eligible booking. The system releases its seats and records a mock refund.

## Payment and Refund Disclaimer

This project uses simulated payments and refunds for demonstration and testing. It does not process real payments or transfer real money.

## Development Status

The backend includes automated tests for the core event booking and organiser workflows. The project can be run locally using the setup instructions above.

## Author

Rohit Aundhakar

## Repository

https://github.com/ROHIT12-Aundhakar/housefull

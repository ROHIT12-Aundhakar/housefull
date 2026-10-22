
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function Dashboard({ events }) {
  const [eventId, setEventId] = useState("");
  const [stats, setStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [dashboardError, setDashboardError] = useState("");
  const [token, setToken] = useState("");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  async function login(event) {
    event.preventDefault();
    setLoginLoading(true);
    setDashboardError("");

    try {
      const response = await fetch(`${API_URL}/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.trim(),
          password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Admin login failed. Check your credentials."
        );
      }

      if (!data.access_token) {
        throw new Error("The server did not return an access token.");
      }

      setToken(data.access_token);
      setPassword("");
      setDashboardError("");
    } catch (err) {
      setDashboardError(
        err.message || "Could not connect to the backend."
      );
    } finally {
      setLoginLoading(false);
    }
  }

  async function loadDashboard(id = eventId, authToken = token) {
    if (!authToken) {
      setDashboardError("Please log in as an admin first.");
      return;
    }

    if (!id) {
      setDashboardError("Please select an event.");
      return;
    }

    setLoadingStats(true);
    setDashboardError("");

    try {
      const response = await fetch(
        `${API_URL}/events/${id}/dashboard`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          setToken("");
          setStats(null);
          throw new Error("Admin login required. Please log in again.");
        }

        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to load dashboard statistics."
        );
      }

      setStats(data);
      setEventId(String(id));
    } catch (err) {
      setDashboardError(
        err.message || "Could not connect to the backend."
      );
    } finally {
      setLoadingStats(false);
    }
  }

  function logout() {
    setToken("");
    setStats(null);
    setEventId("");
    setPassword("");
    setDashboardError("");
  }

  const cards = stats
    ? [
        { label: "Total Seats", value: stats.total_seats, icon: "🪑" },
        { label: "Available Seats", value: stats.available_seats, icon: "🟢" },
        { label: "Held Seats", value: stats.held_seats, icon: "🟡" },
        { label: "Booked Seats", value: stats.booked_seats, icon: "🎟️" },
        {
          label: "Confirmed Bookings",
          value: stats.confirmed_bookings,
          icon: "✅",
        },
        {
          label: "Total Revenue",
          value: `₹${Number(stats.total_revenue ?? 0).toLocaleString("en-IN")}`,
          icon: "💰",
        },
        {
          label: "Checked-in Attendees",
          value: stats.checked_in_count,
          icon: "🚪",
        },
      ]
    : [];

  const occupancy =
    stats && Number(stats.total_seats) > 0
      ? Math.min(
          100,
          Math.round((stats.booked_seats / stats.total_seats) * 100)
        )
      : 0;

  return (
    <section className="seat-section admin-section" id="admin-dashboard">
      <div className="section-heading">
        <div>
          <span className="eyebrow">EVENT MANAGEMENT</span>
          <h2>
            Admin Dashboard<span>.</span>
          </h2>
          <p>Monitor bookings, revenue, seats, and attendance.</p>
        </div>

        {token && (
          <button
            type="button"
            className="close-button"
            onClick={logout}
          >
            Admin Logout
          </button>
        )}
      </div>

      {!token ? (
        <form className="booking-summary" onSubmit={login}>
          <span className="eyebrow">RESTRICTED ACCESS</span>
          <h3>Admin Login</h3>
          <p>Sign in to access the administrator dashboard.</p>

          <div className="customer-fields">
            <label htmlFor="admin-username">Username</label>
            <input
              id="admin-username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter admin username"
              required
              disabled={loginLoading}
            />

            <label htmlFor="admin-password">Password</label>
            <input
              id="admin-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter admin password"
              required
              disabled={loginLoading}
            />
          </div>

          {dashboardError && (
            <p className="message error" role="alert">
              {dashboardError}
            </p>
          )}

          <button
            type="submit"
            className="book-button"
            disabled={loginLoading}
          >
            {loginLoading ? "Signing in..." : "Admin Login →"}
          </button>
        </form>
      ) : (
        <div className="booking-summary">
          <p className="summary-note">
            You are signed in as an administrator.
          </p>

          <div className="customer-fields">
            <label htmlFor="dashboard-event">Select event</label>
            <select
              id="dashboard-event"
              value={eventId}
              onChange={(event) => {
                setEventId(event.target.value);
                setStats(null);
                setDashboardError("");
              }}
            >
              <option value="">Choose an event</option>
              {events.map((event) => (
                <option key={event.id} value={event.id}>
                  {event.name || event.event_name} (ID: {event.id})
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="book-button"
            onClick={() => loadDashboard()}
            disabled={loadingStats || !eventId}
          >
            {loadingStats
              ? "Loading statistics..."
              : "Load / Refresh Dashboard ↻"}
          </button>

          {dashboardError && (
            <p className="message error" role="alert">
              {dashboardError}
            </p>
          )}

          {stats && (
            <>
              <h3>{stats.event_name}</h3>
              <p className="summary-note">
                Event ID: {stats.event_id}. Refresh to get the latest figures.
              </p>

              <div className="admin-stats-grid">
                {cards.map((card) => (
                  <article className="admin-stat-card" key={card.label}>
                    <span className="admin-stat-icon">{card.icon}</span>
                    <p>{card.label}</p>
                    <h3>{card.value ?? 0}</h3>
                  </article>
                ))}
              </div>

              <div className="admin-progress">
                <div className="admin-progress-heading">
                  <span>Seat occupancy</span>
                  <strong>{occupancy}%</strong>
                </div>

                <div
                  className="admin-progress-track"
                  role="progressbar"
                  aria-label="Seat occupancy"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={occupancy}
                >
                  <div
                    className="admin-progress-fill"
                    style={{ width: `${occupancy}%` }}
                  />
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

function App() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);

  const [loading, setLoading] = useState(true);
  const [seatsLoading, setSeatsLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);

  const [error, setError] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");

  const [bookingResult, setBookingResult] = useState(null);
  const [bookingError, setBookingError] = useState("");
  const [paymentMessage, setPaymentMessage] = useState("");
  const [ticket, setTicket] = useState(null);

  const [ticketCode, setTicketCode] = useState("");
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [checkinResult, setCheckinResult] = useState(null);
  const [checkinError, setCheckinError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/events`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load events.");
        return response.json();
      })
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => {
        setError("Unable to connect to Housefull. Check your backend.");
      })
      .finally(() => setLoading(false));
  }, []);

  async function refreshSeats(eventId) {
    const response = await fetch(`${API_URL}/events/${eventId}/seats`);

    if (response.ok) {
      const data = await response.json();
      setSeats(Array.isArray(data) ? data : data.seats ?? []);
    }
  }

  async function openEvent(event) {
    setSelectedEvent(event);
    setSeats([]);
    setSelectedSeats([]);
    setBookingResult(null);
    setBookingError("");
    setPaymentMessage("");
    setTicket(null);
    setError("");
    setSeatsLoading(true);

    try {
      await refreshSeats(event.id);
    } catch {
      setError("Unable to load seats. Please try again.");
    } finally {
      setSeatsLoading(false);
    }
  }

  function toggleSeat(seat) {
    if (seat.status?.toLowerCase() !== "available") return;

    setSelectedSeats((previous) =>
      previous.includes(seat.id)
        ? previous.filter((id) => id !== seat.id)
        : [...previous, seat.id]
    );

    setBookingResult(null);
    setBookingError("");
    setPaymentMessage("");
    setTicket(null);
  }

  function getErrorMessage(data, fallback) {
    const detail = data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join(", ");
    }

    if (detail && typeof detail.message === "string") {
      return detail.message;
    }

    return fallback;
  }

  async function holdSeats() {
    if (!customerName.trim() || !customerEmail.trim()) {
      setBookingError("Please enter your name and email.");
      return;
    }

    const email = customerEmail.trim();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setBookingError("Please enter a valid email address.");
      return;
    }

    if (selectedSeats.length === 0) {
      setBookingError("Please select at least one available seat.");
      return;
    }

    setBookingLoading(true);
    setBookingError("");
    setPaymentMessage("");
    setTicket(null);

    try {
      const response = await fetch(`${API_URL}/bookings/hold`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: customerName.trim(),
          customer_email: email,
          seat_ids: selectedSeats,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Unable to hold seats. Please try again.")
        );
      }

      setBookingResult(data);
      setSelectedSeats([]);
      await refreshSeats(selectedEvent.id);
    } catch (err) {
      setBookingError(
        err.message || "Could not connect to the booking server."
      );
    } finally {
      setBookingLoading(false);
    }
  }

  async function processPayment(paymentStatus) {
    if (!bookingResult?.booking_code || paymentLoading) return;

    setPaymentLoading(true);
    setPaymentMessage("");
    setBookingError("");
    setTicket(null);

    try {
      const response = await fetch(`${API_URL}/payments/mock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          booking_code: bookingResult.booking_code,
          payment_status: paymentStatus,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Payment could not be processed.")
        );
      }

      setBookingResult((previous) =>
        previous ? { ...previous, ...data } : previous
      );

      if (paymentStatus === "fail") {
        setPaymentMessage(
          "Mock payment failed. Your held seats have been released. Please select your seats and start a new booking."
        );
        setBookingResult(null);
        await refreshSeats(selectedEvent.id);
        return;
      }

      setPaymentMessage("Payment successful! Loading your ticket...");

      const ticketResponse = await fetch(
        `${API_URL}/tickets/${encodeURIComponent(data.booking_code)}`
      );

      const ticketData = await ticketResponse.json().catch(() => ({}));

      if (!ticketResponse.ok) {
        throw new Error(
          getErrorMessage(
            ticketData,
            "Payment succeeded, but the ticket could not be loaded. Try refreshing."
          )
        );
      }

      setTicket(ticketData);
      setPaymentMessage("Booking confirmed! Your ticket is ready.");
      await refreshSeats(selectedEvent.id);
    } catch (err) {
      setPaymentMessage(
        err.message || "Could not connect to the payment server."
      );
    } finally {
      setPaymentLoading(false);
    }
  }

  async function checkInTicket(event) {
    event.preventDefault();

    const code = ticketCode.trim();

    if (!code) {
      setCheckinError("Please enter a ticket code.");
      setCheckinResult(null);
      return;
    }

    setCheckinLoading(true);
    setCheckinError("");
    setCheckinResult(null);

    try {
      const response = await fetch(
        `${API_URL}/check-in/${encodeURIComponent(code)}`,
        { method: "POST" }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Check-in failed. Verify the ticket code.")
        );
      }

      setCheckinResult(data);
      setTicketCode("");
    } catch (err) {
      setCheckinError(
        err.message || "Could not connect to the check-in server."
      );
    } finally {
      setCheckinLoading(false);
    }
  }

  function formatDate(date) {
    if (!date) return "Date to be announced";

    return new Date(date).toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  const selectedSeatDetails = seats.filter((seat) =>
    selectedSeats.includes(seat.id)
  );

  const totalPrice = selectedSeatDetails.reduce(
    (total, seat) =>
      total + Number(seat.price ?? seat.price_per_seat ?? 0),
    0
  );

  function startNewBooking() {
    setBookingResult(null);
    setBookingError("");
    setPaymentMessage("");
    setTicket(null);
    setSelectedSeats([]);
  }

  return (
    <div className="app">
      <header className="navbar">
        <a className="logo" href="#">
          HOUSE<span>FULL</span>
        </a>
        <span className="nav-label">YOUR NEXT EXPERIENCE STARTS HERE</span>
      </header>

      <main>
        <section className="hero">
          <div className="hero-content">
            <span className="eyebrow">BOOK. EXPERIENCE. REPEAT.</span>
            <h1>
              Your seat.
              <br />
              Your <span>experience.</span>
            </h1>
            <p>
              Discover events, choose your favourite seats, and make
              every moment count.
            </p>
            <a className="primary-button" href="#events">
              Explore Events ↗
            </a>
          </div>

          <div className="hero-decoration" aria-hidden="true">
            <div className="ticket-art">
              <span>H</span>
              <div>
                YOUR NEXT
                <br />
                GREAT MEMORY
              </div>
              <small>ADMIT ONE</small>
            </div>
          </div>
        </section>

        <section className="events-section" id="events">
          <div className="section-heading">
            <div>
              <span className="eyebrow">FIND YOUR NEXT PLAN</span>
              <h2>
                Upcoming events<span>.</span>
              </h2>
            </div>
            <span className="event-count">
              {events.length} {events.length === 1 ? "EVENT" : "EVENTS"}
            </span>
          </div>

          {loading && <p className="message">Loading events...</p>}

          {!loading && error && !selectedEvent && (
            <div className="message error">
              {error}
              <button onClick={() => window.location.reload()}>Retry</button>
            </div>
          )}

          {!loading && !error && events.length === 0 && (
            <div className="empty-state">
              <h3>No events found</h3>
              <p>Create an event through your backend API to see it here.</p>
            </div>
          )}

          <div className="event-grid">
            {events.map((event) => (
              <article className="event-card" key={event.id}>
                <div className="event-art">
                  <span className="event-tag">LIVE EXPERIENCE</span>
                  <div className="event-art-letter">H.</div>
                  <span className="event-art-bottom">MAKE IT A MOMENT</span>
                </div>

                <div className="event-info">
                  <span className="event-date">{formatDate(event.starts_at)}</span>
                  <h3>{event.name || event.event_name}</h3>
                  <p>{event.venue || "Venue to be announced"}</p>
                  <button
                    className="book-button"
                    onClick={() => openEvent(event)}
                  >
                    Select seats <span>↗</span>
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        {selectedEvent && (
          <section className="seat-section" id="seat-selection">
            <div className="section-heading">
              <div>
                <span className="eyebrow">MAKE IT YOURS</span>
                <h2>
                  Select your seats<span>.</span>
                </h2>
                <p>{selectedEvent.name || selectedEvent.event_name}</p>
              </div>

              <button
                className="close-button"
                onClick={() => {
                  setSelectedEvent(null);
                  setSeats([]);
                  setSelectedSeats([]);
                  setBookingResult(null);
                  setBookingError("");
                  setPaymentMessage("");
                  setTicket(null);
                  setError("");
                }}
              >
                Close ×
              </button>
            </div>

            <div className="seat-legend">
              <span><i className="legend-dot available" /> Available</span>
              <span><i className="legend-dot booked" /> Booked</span>
              <span><i className="legend-dot held" /> Held</span>
            </div>

            {seatsLoading ? (
              <p className="message">Loading seats...</p>
            ) : error && selectedEvent ? (
              <div className="message error">
                {error}
                <button onClick={() => openEvent(selectedEvent)}>Retry</button>
              </div>
            ) : seats.length === 0 ? (
              <p className="message">No seats found for this event.</p>
            ) : (
              <>
                <div className="seat-grid">
                  {seats.map((seat) => {
                    const isSelected = selectedSeats.includes(seat.id);
                    const isAvailable =
                      seat.status?.toLowerCase() === "available";

                    return (
                      <button
                        type="button"
                        key={seat.id}
                        className={`seat-item ${isSelected ? "selected" : ""} ${
                          !isAvailable ? "unavailable" : ""
                        }`}
                        disabled={
                          !isAvailable || bookingLoading || paymentLoading
                        }
                        onClick={() => toggleSeat(seat)}
                        aria-pressed={isSelected}
                      >
                        <span className="seat-name">
                          {seat.row_label ?? seat.row ?? ""}
                          {seat.seat_number}
                        </span>
                        <span className="seat-price">
                          ₹{seat.price ?? seat.price_per_seat ?? "—"}
                        </span>
                        <span
                          className={`seat-status ${
                            isSelected
                              ? "selected-status"
                              : seat.status || "unknown"
                          }`}
                        >
                          {isSelected ? "Selected" : seat.status || "Unknown"}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {selectedSeats.length > 0 && !bookingResult && !ticket && (
                  <div className="booking-summary">
                    <span className="eyebrow">YOUR SELECTION</span>
                    <h3>Booking Summary</h3>
                    <p>
                      Selected seats: <strong>{selectedSeats.length}</strong>
                    </p>
                    <p>
                      Seats:{" "}
                      <strong>
                        {selectedSeatDetails
                          .map(
                            (seat) =>
                              `${seat.row_label ?? seat.row ?? ""}${seat.seat_number}`
                          )
                          .join(", ")}
                      </strong>
                    </p>
                    <p className="booking-total">Total: ₹{totalPrice.toFixed(2)}</p>

                    <div className="customer-fields">
                      <label htmlFor="customer-name">Full name</label>
                      <input
                        id="customer-name"
                        type="text"
                        autoComplete="name"
                        value={customerName}
                        onChange={(event) => setCustomerName(event.target.value)}
                        placeholder="Enter your full name"
                        disabled={bookingLoading}
                      />

                      <label htmlFor="customer-email">Email address</label>
                      <input
                        id="customer-email"
                        type="email"
                        autoComplete="email"
                        value={customerEmail}
                        onChange={(event) => setCustomerEmail(event.target.value)}
                        placeholder="Enter your email"
                        disabled={bookingLoading}
                      />
                    </div>

                    {bookingError && (
                      <p className="message error" role="alert">
                        {bookingError}
                      </p>
                    )}

                    <button
                      type="button"
                      className="book-button"
                      onClick={holdSeats}
                      disabled={bookingLoading}
                    >
                      {bookingLoading ? "Holding seats..." : "Continue to Booking →"}
                    </button>
                    <p className="summary-note">
                      Seats are held temporarily for 5 minutes.
                    </p>
                  </div>
                )}

                {bookingResult && !ticket && (
                  <div className="booking-summary" role="status">
                    <span className="eyebrow">STEP 2 · MOCK PAYMENT</span>
                    <h3>Seats held successfully!</h3>
                    <p>
                      Booking code: <strong>{bookingResult.booking_code}</strong>
                    </p>
                    <p>
                      Amount:{" "}
                      <strong>
                        ₹{Number(bookingResult.total_amount ?? 0).toFixed(2)}
                      </strong>
                    </p>
                    <p>Status: <strong>{bookingResult.status}</strong></p>
                    <p className="summary-note">
                      This is a simulated payment for project testing, not a
                      real payment. Complete it before the 5-minute hold expires.
                    </p>

                    {bookingError && (
                      <p className="message error" role="alert">
                        {bookingError}
                      </p>
                    )}

                    <div className="payment-actions">
                      <button
                        type="button"
                        className="book-button"
                        onClick={() => processPayment("success")}
                        disabled={paymentLoading}
                      >
                        {paymentLoading
                          ? "Processing..."
                          : "✓ Simulate Successful Payment"}
                      </button>
                      <button
                        type="button"
                        className="close-button"
                        onClick={() => processPayment("fail")}
                        disabled={paymentLoading}
                      >
                        Simulate Failed Payment
                      </button>
                    </div>
                  </div>
                )}

                {paymentMessage && (
                  <p
                    className={`message ${ticket ? "" : "error"}`}
                    role="status"
                  >
                    {paymentMessage}
                  </p>
                )}

                {ticket && (
                  <div className="booking-summary ticket-card">
                    <span className="eyebrow">HOUSEFULL · E-TICKET</span>
                    <h2>You're going!</h2>
                    <p>Your booking is confirmed. Keep this ticket ready.</p>

                    <div className="ticket-qr">
                      <img
                        src={ticket.qr_code}
                        alt="Ticket QR code for staff check-in"
                        width="220"
                        height="220"
                      />
                    </div>

                    <h3>{selectedEvent.name || selectedEvent.event_name}</h3>
                    <p>{selectedEvent.venue || "Venue to be announced"}</p>
                    <p>{formatDate(selectedEvent.starts_at)}</p>

                    <div className="ticket-details">
                      <p><strong>Customer:</strong> {ticket.customer_name}</p>
                      <p><strong>Email:</strong> {ticket.customer_email}</p>
                      <p><strong>Booking code:</strong> {ticket.booking_code}</p>
                      <p><strong>Ticket code:</strong> {ticket.ticket_code}</p>
                      <p>
                        <strong>Seats:</strong>{" "}
                        {ticket.seats
                          ?.map((seat) => `${seat.row}${seat.seat_number}`)
                          .join(", ")}
                      </p>
                      <p className="booking-total">
                        Total: ₹{Number(ticket.total_amount).toFixed(2)}
                      </p>
                      <p>
                        <strong>Status:</strong>{" "}
                        <span className="selected-status">{ticket.status}</span>
                      </p>
                    </div>

                    <p className="summary-note">
                      Show this QR code to event staff for check-in.
                    </p>

                    <button
                      type="button"
                      className="book-button"
                      onClick={() => window.print()}
                    >
                      Print Ticket / Save as PDF
                    </button>
                    <button
                      type="button"
                      className="close-button"
                      onClick={startNewBooking}
                    >
                      Start another booking
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {/* TICKET CHECK-IN */}
        <section className="seat-section checkin-section" id="check-in">
          <div className="section-heading">
            <div>
              <span className="eyebrow">EVENT STAFF</span>
              <h2>
                Ticket check-in<span>.</span>
              </h2>
              <p>Validate a confirmed ticket at the event entrance.</p>
            </div>
          </div>

          <form className="booking-summary" onSubmit={checkInTicket}>
            <div className="customer-fields">
              <label htmlFor="ticket-code">Ticket code</label>
              <input
                id="ticket-code"
                type="text"
                value={ticketCode}
                onChange={(event) => {
                  setTicketCode(event.target.value);
                  setCheckinError("");
                  setCheckinResult(null);
                }}
                placeholder="Enter the ticket code"
                autoComplete="off"
                disabled={checkinLoading}
              />
            </div>

            {checkinError && (
              <p className="message error" role="alert">
                {checkinError}
              </p>
            )}

            {checkinResult && (
              <div className="ticket-details" role="status">
                <h3>Check-in successful!</h3>
                <p>
                  <strong>Customer:</strong>{" "}
                  {checkinResult.customer_name ?? "Confirmed"}
                </p>
                {checkinResult.seats && (
                  <p>
                    <strong>Seats:</strong>{" "}
                    {Array.isArray(checkinResult.seats)
                      ? checkinResult.seats
                          .map((seat) =>
                            typeof seat === "string"
                              ? seat
                              : `${seat.row ?? ""}${seat.seat_number ?? ""}`
                          )
                          .join(", ")
                      : String(checkinResult.seats)}
                  </p>
                )}
                <p><strong>Result:</strong> Attendee checked in.</p>
              </div>
            )}

            <button
              type="submit"
              className="book-button"
              disabled={checkinLoading}
            >
              {checkinLoading ? "Verifying ticket..." : "Verify & Check In →"}
            </button>
            <p className="summary-note">
              Enter the ticket code, not the booking code.
            </p>
          </form>
        </section>

        <Dashboard events={events} />
      </main>

      <footer className="footer">
        <a className="logo" href="#">
          HOUSE<span>FULL</span>
        </a>
        <p>Good events. Great memories.</p>
      </footer>
    </div>
  );
}

export default App;

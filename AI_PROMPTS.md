# AI_PROMPTS.md

## 1. AI Tools Used

- **Tool:** ChatGPT
- **Purpose:** Software development assistance, API implementation, debugging, automated testing, code review, documentation, and version control guidance.
- **Technologies:** Python, FastAPI, SQLAlchemy, PostgreSQL, SQLite, React, JavaScript, and Git.

## 2. Development Prompts and Their Outcomes

The following are representative prompts describing the development tasks performed during this project. They are professionally phrased summaries, not verbatim historical prompts.

| No. | Development Prompt | Purpose | Outcome |
|---|---|---|---|
| 1 | Design a FastAPI backend architecture for an event ticket booking system using SQLAlchemy and PostgreSQL. | Establish the backend architecture and database integration. | Used as the foundation for the backend implementation. |
| 2 | Implement event management APIs with database models, request validation, and appropriate HTTP responses. | Support event creation and retrieval. | Implemented and tested the event APIs. |
| 3 | Develop a seat reservation mechanism with temporary holds, expiration handling, and duplicate-booking prevention. | Prevent conflicting seat reservations. | Implemented seat holds and reservation checks. |
| 4 | Integrate mock payment processing with successful and failed payment scenarios, booking status updates, and seat release logic. | Simulate the ticket payment workflow. | Implemented and tested both payment outcomes. |
| 5 | Implement ticket generation, QR-code support, and check-in validation with duplicate check-in prevention. | Support ticket verification at event entry. | Implemented ticket retrieval and check-in functionality. |
| 6 | Add administrator authentication using JWT and protect event management, dashboard, and booking cancellation endpoints. | Restrict administrative operations to authenticated users. | Implemented protected administrative APIs. |
| 7 | Create an event dashboard that reports booking statistics, seat availability, revenue, ticket status, check-in details, and refund records. | Provide administrators with event-level reporting. | Implemented the dashboard endpoint. |
| 8 | Implement booking cancellation with seat release, refund record creation, and validation against invalid or duplicate cancellation requests. | Support controlled cancellation and simulated refunds. | Implemented cancellation and mock refund handling. |
| 9 | Develop automated API tests using an isolated SQLite database to verify booking workflows, authentication, cancellation, and data cleanup. | Validate functionality without modifying the main database. | Created and executed the automated test suite. |
| 10 | Review failing test assertions, identify mismatches between API response schemas and database models, and correct the tests based on the actual implementation. | Resolve test failures accurately. | Corrected the seat hold expiration assertion; all 10 tests passed. |
| 11 | Configure the React frontend to communicate with the FastAPI backend and display event information, seat selection, and booking states. | Connect the user interface to the backend APIs. | Integrated the frontend with the local API. |
| 12 | Review repository hygiene, prepare submission metadata, document AI assistance, and verify the final Git commit and release tag. | Prepare the project repository for submission. | Added submission documentation and managed the Git tag. |

## 3. AI-Generated Code Review and Corrections

### Example 1: API Response Schema Mismatch

- **Issue:** A test attempted to access `hold_expires_at` in the seat API response, but the response schema did not expose that field.
- **Detection:** The automated test failed with `KeyError: 'hold_expires_at'`.
- **Correction:** Updated the test to inspect the `Seat` model directly through a database session in the isolated test database.
- **Verification:** The full test suite passed after the correction.

### Example 2: Cross-Origin Resource Sharing (CORS)

- **Issue encountered:** A browser request from the frontend was blocked because the backend response did not include the required CORS headers.
- **Detection:** The browser console reported a CORS policy error.
- **Resolution:** Configured FastAPI CORS middleware to allow requests from the development frontend.
- **Verification:** The frontend successfully communicated with the backend after the configuration was corrected.

### Example 3: Database Connection and Startup Validation

- **Issue encountered:** The backend experienced a database connection/startup error during initial setup.
- **Detection:** The terminal displayed a Python traceback during database initialization.
- **Resolution:** Investigated the database configuration and connection setup, then verified connectivity before continuing development.
- **Verification:** The database connection succeeded, tables were created, and the API started successfully.

*Note: Examples 2 and 3 document development issues encountered and resolved. They should not be interpreted as proof that the original implementation of each issue was generated by AI.*

## 4. Automated Testing

**Command used:**

```bash
python -m pytest -v
```

**Latest verified result:** 10 passed, 1 warning.

The automated tests cover:

- Event creation and seat reservation.
- Successful and failed mock payments.
- Ticket generation and check-in.
- Duplicate booking and payment prevention.
- Administrator authentication.
- Booking cancellation and simulated refunds.
- Dashboard statistics and booking details.
- Event deletion and booking-data reset.

The warning concerned a deprecated testing dependency integration and did not cause test failures.

## 5. Human Review and Verification

- Reviewed API behavior and automated test results.
- Corrected the failing test assertion based on the actual response schema.
- Verified that automated tests use a separate SQLite database.
- Committed and pushed project changes to GitHub.
- Created and verified the `final` Git tag.

## 6. Limitations

- Payment processing and refunds are simulated; no real financial transactions occur.
- The application has not been confirmed as deployed.
- The submission metadata uses a null application URL because a deployment URL was not available.
- The prompts above are professional summaries of development tasks, not a complete verbatim transcript of every AI interaction.
# Visitor Hub

A containerized visitor check-in demo. Visitors submit their details, verify an email address with a one-time code, and receive a time-limited QR gate pass. Gate staff can validate each pass once, and the frontend shows basic visitor totals.

## Run with Docker Compose

1. Copy `.env.example` to `.env` and replace the sample passwords and `APP_SECRET` with local values. `APP_SECRET` should be a random value with at least 32 characters.
2. Start the stack from the project root:

   ```sh
   docker compose up --build
   ```

3. Open [http://localhost:8080](http://localhost:8080). The API docs are available at [http://localhost:8080/docs](http://localhost:8080/docs).

In the default development configuration, the backend logs an OTP and also returns it to the UI so the flow works without an email account. To deliver real email, set `OTP_DELIVERY=smtp` in `.env` and configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM`. Never use console delivery in production; set `APP_ENV=production` and configure SMTP. Keep `.env` private.

MySQL initializes from `Backend/init.sql` when its data volume is first created. If you change the schema after the volume has been initialized, apply the SQL migration to your existing database; initialization scripts do not rerun against an existing volume.

## Flow and API

- `POST /api/submit_form` saves visitor details and sends a six-digit email code.
- `POST /api/verify_otp` checks the code and issues an eight-hour QR pass.
- `POST /api/validate_pass` validates and consumes a pass once at the gate.
- `GET /api/analyse_visitors` returns visitor, verification, and pass counts for a date range (defaults to the last 30 days).
- `GET /api/health` checks API and database availability.

The QR code contains an opaque token. Only its keyed hash is stored in MySQL. Email OTP values are also stored as keyed hashes. Configure a unique `APP_SECRET` before using persistent data, and preserve it when restarting the service so issued tokens remain verifiable.

## Services

- `frontend`: static HTML, CSS, and JavaScript served by Nginx on port 8080. Nginx forwards `/api` and `/docs` to FastAPI.
- `backend`: FastAPI on the Compose network, connected to MySQL.
- `mysql`: MySQL 8 with a named volume for persistent data.

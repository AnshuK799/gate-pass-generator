# DYPIU Visitor Hub

A responsive visitor check-in experience for DY Patil International University. Visitors verify their email, submit their visit details, and receive an on-screen QR pass.

## Run the application

1. Copy `.env.example` to `.env` and set `MYSQL_ROOT_PASSWORD` and `DB_PASSWORD` to local values.
2. Start all services from the project root:

   ```sh
   docker compose up --build
   ```

3. Open [http://localhost:8080](http://localhost:8080). The API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

By default, OTP delivery uses the development console mode. The code appears in the check-in screen and backend logs; view logs with:

```sh
docker compose logs -f backend
```

To send real email, set `OTP_DELIVERY=smtp` and fill in `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM` in `.env`, then restart the stack. OTPs expire after five minutes.

MySQL initializes its schema from `Backend/init.sql` on the first start and keeps data in the `mysql_data` volume. Initialization scripts do not run again for an existing volume.

## Services

- `frontend`: static HTML, CSS, and JavaScript served by Python on port 8080.
- `backend`: FastAPI on port 8000, connected to MySQL.
- `mysql`: MySQL 8 with persistent named storage.

No Nginx service is used. The frontend calls the backend at `http://localhost:8000`.

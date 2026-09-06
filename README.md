# Samunnathi — Full Application

## 1. What I found when I inspected your project

The uploaded project (`samunnathi-homepage.zip`) was a **static site only**:
plain HTML/CSS/JS, no Flask app, no database, no admin, no forms. There was
no existing backend to extend — so "existing architecture" here means the
homepage's **visual design and button links**, which are the only things I
was asked not to touch.

What I preserved exactly, unchanged:
- The homepage's HTML structure, every section, the hero, cards, footer
- All CSS in `static/assets/css/*` (colors, type, spacing, animations)
- All JS behavior (mobile drawer, auto-scroll strips, count-up stats)
- The logo, onsite/founder/event placeholder images

What I changed on the homepage (only this):
- `Get Guidance` → now points to `/guidance` (was `/get-guidance`)
- `Become a Mentor` → now points to `/mentor` (was `/become-a-mentor`)
- `Become a Volunteer` → now points to `/volunteer` (was `/become-a-volunteer`)
- Asset paths now use Flask's `url_for('static', ...)` instead of relative
  paths, since the site is now served by Flask rather than opened as a
  plain file.

Everything else described in the brief (backend, database, forms, admin,
email, resumes) did not exist before, so it's new.

## 2. What was implemented

- **Public pages**: `/guidance`, `/mentor`, `/volunteer` — info page + form
  each, styled with the same design tokens as the homepage (same CSS
  variables, buttons, cards, spacing).
- **Backend**: Flask, blueprint-per-concern (`routes/public.py`,
  `guidance.py`, `mentor.py`, `volunteer.py`, `auth.py`, `admin.py`).
- **Database**: MySQL via SQLAlchemy (`models/`), with `schema.sql` for
  manual setup. Falls back to a local SQLite file if MySQL isn't configured,
  so you can try it immediately without installing MySQL.
- **Resume upload**: extension check + real file-content signature check
  (not just the extension) + 5&nbsp;MB limit + a randomly generated stored
  filename. Files live in `uploads/resumes/`, **outside** `static/`, and are
  only reachable through authenticated admin routes.
- **Admin dashboard**: stats, recent applications, recent notifications,
  per-type lists with search/filter/pagination, detail pages, status
  changes, resume view/download, reply-by-email, resend-confirmation,
  delete (with resume file cleanup), CSV/Excel/PDF exports.
- **Notifications**: created on every submission, bell counter in the
  topbar, a polling endpoint (`/admin/notifications/poll`) the dashboard
  calls every 15s to update the count and toast new ones — no WebSockets.
- **Email**: SMTP confirmation email sent automatically on submission.
  A failed send is logged to `email_logs` and never deletes or blocks the
  application — admins get a "Resend Confirmation Email" button.
- **Security**: hashed admin passwords (Flask-Login), CSRF protection on
  every form (Flask-WTF), parameterized queries (SQLAlchemy ORM), resume
  content-signature validation, path-traversal-safe file serving, no
  internal errors ever shown to the user (404/413/500 pages), a lightweight
  duplicate-submission guard.

## 3. Files created

```
app.py, config.py, requirements.txt, schema.sql, .env.example, .gitignore,
create_admin.py

routes/           public.py, guidance.py, mentor.py, volunteer.py, auth.py, admin.py
models/           user.py, guidance.py, mentor.py, volunteer.py, notification.py,
                  email_log.py, reference.py, __init__.py
services/         email_service.py, notification_service.py, export_service.py,
                  file_service.py, validators.py, dedupe.py

templates/        base.html, home.html, guidance.html, mentor.html, volunteer.html,
                  success.html, errors/404.html, errors/413.html, errors/500.html
templates/admin/  base.html, login.html, change_password.html, dashboard.html,
                  guidance_list.html, guidance_details.html,
                  mentor_list.html, mentor_details.html,
                  volunteer_list.html, volunteer_details.html,
                  notifications.html, _list_macros.html, _detail_actions.html

static/assets/css/forms.css       new (form + flash + info-page styles)
static/assets/js/forms.js         new (progressive-enhancement form JS)
static/admin/css/admin.css        new (admin layout)
static/admin/js/admin.js          new (notification polling + toasts)

uploads/resumes/    private upload directory (not in static/)
```

## 4. Files modified

- `index.html` → became `templates/base.html` + `templates/home.html`
  (split so Flask can render it; content and design are identical). The
  original `index.html` is no longer used directly — Flask serves the
  Jinja version.
- Three button `href`s updated as described in section 1.
- Asset `<link>`/`<img>`/`<script>` paths now use `url_for('static', ...)`.

Nothing else was touched: colors, typography, spacing, cards, hero,
footer, and JS behavior (auto-scroll, drawer, counters) are byte-for-byte
the same design as before.

## 5. Database schema

See `schema.sql` for the full MySQL DDL (tables: `admins`,
`guidance_requests`, `mentor_applications`, `volunteer_applications`,
`notifications`, `email_logs` — matches what you specified, including all
requested indexes). SQLAlchemy models in `models/` mirror this exactly and
can also create the schema automatically (see setup below).

## 6. Local setup

```bash
cd samunnathi
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: at minimum set SECRET_KEY. Leave MYSQL_HOST blank to use
# SQLite for a quick local check, or fill in MYSQL_* to use real MySQL.
```

### Using MySQL (recommended for anything beyond a quick check)

```bash
mysql -u root -p < schema.sql
# Then set MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE in .env
```

SQLAlchemy will also create any missing tables automatically on first run
via `db.create_all()` (called by `create_admin.py` and on `python app.py`
startup) — `schema.sql` is there for manual setup, review, and migrations.

### Create your first admin account

```bash
python create_admin.py
# or non-interactively:
python create_admin.py --name "Admin" --email admin@samunnathi.org --password "a-strong-password"
```

### Run it

```bash
python app.py
# visit http://localhost:5000
# admin at http://localhost:5000/admin/login
```

## 7. Email configuration

Fill in `.env`:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-address@gmail.com
MAIL_PASSWORD=an-app-password        # not your normal password
MAIL_DEFAULT_SENDER=your-address@gmail.com
```
For Gmail, generate an **App Password** (requires 2-Step Verification on
the account) rather than using the account password directly. Any standard
SMTP provider (SendGrid, Mailgun, Amazon SES, your host's SMTP) works the
same way — just change `MAIL_SERVER`/`MAIL_PORT`.

If email isn't configured, or a send fails, the application is still saved
and visible in the admin dashboard — you'll see it logged in the
`email_logs` table and can hit "Resend Confirmation Email" from the
application's detail page once email is fixed.

## 8. Resume upload configuration

- Allowed formats: PDF, DOC, DOCX (validated by real file content, not just
  the extension).
- Max size: 5&nbsp;MB (`RESUME_MAX_SIZE_BYTES` in `config.py`).
- Storage location: `UPLOAD_FOLDER` in `.env` (defaults to
  `uploads/resumes/`, outside `static/` — never publicly served).
- In production, make sure this directory is writable by the app process
  and is **not** inside any directory your web server serves directly.

## 9. Testing performed

Ran automated end-to-end checks against a live instance of this exact code:

- All three forms (guidance/mentor/volunteer) submit successfully, create
  the correct DB row, notification, and (attempted) confirmation email;
  reference numbers generate correctly (`GUID-000001`, `MENTOR-000001`,
  `VOL-000001`, ...).
- Server-side validation rejects missing/invalid fields (400, friendly
  message, no traceback).
- CSRF-less POSTs are rejected (400).
- Resume upload: valid PDF, DOC, and DOCX accepted; a renamed executable
  (wrong file content behind a `.pdf` extension) is rejected by the
  content-signature check; `.exe` is rejected outright; a 6&nbsp;MB file is
  rejected for exceeding the 5&nbsp;MB limit.
- Duplicate-submission guard: a failed attempt does **not** block your next
  real attempt; a genuinely rapid duplicate of a *successful* submission is
  blocked for 20 seconds.
- Admin: login required for all `/admin/*` routes (unauthenticated access
  redirects to login, verified on the resume routes specifically); login/
  logout/change-password; dashboard stats; guidance/mentor/volunteer detail
  pages; status changes persist; resume view/download work only when
  authenticated and are **not** reachable under `/static/`; CSV, Excel, and
  PDF exports all return valid non-empty files; delete removes the DB row
  and the resume file together, and doesn't affect other applications;
  resend-confirmation and reply-by-email both work and log to
  `email_logs`.
- No horizontal overflow at 390px, 768px, or 1440px on the homepage or any
  of the three new pages (checked with a headless browser).

What I did **not** independently re-verify: real SMTP delivery (no mail
credentials in this environment — the send path is exercised and logs
correctly, but you should send yourself a real test email once you fill in
`.env`), and real MySQL (tested against SQLite via the same SQLAlchemy code
path — this is the standard way to validate ORM code, but run through the
checklist below once against your real MySQL instance before going live).

### Suggested checklist for your own MySQL instance

1. `mysql -u root -p < schema.sql`, set `.env`, run `python create_admin.py`.
2. Submit each of the three forms once from the actual homepage.
3. Confirm rows appear in `guidance_requests` / `mentor_applications` /
   `volunteer_applications` and a notification appears in the admin bell.
4. Confirm a real email arrives at the address you submitted.
5. Log in to `/admin/login`, open each application, change its status,
   download its PDF, and (for mentor) view/download the resume.
6. Try the CSV/Excel exports on each list page.

## 10. Deployment

This is a standard Flask app — deploy it however you'd deploy any Flask
app. A minimal path:

```bash
pip install -r requirements.txt
export FLASK_ENV=production
export SESSION_COOKIE_SECURE=true   # once served over HTTPS
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Put a reverse proxy (nginx, Caddy, or your host's built-in proxy) in front
of gunicorn for HTTPS termination and to serve `/static/` efficiently.
Make sure `uploads/resumes/` is **not** inside any path the reverse proxy
serves directly.

Set every value in `.env` for production (`SECRET_KEY` especially — generate
a long random value, e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).

Any host that runs a standard Python/WSGI app works: a VPS, Render,
Railway, PythonAnywhere, or similar. For MySQL, most of these offer a
managed MySQL add-on, or you can point `MYSQL_HOST` at any reachable MySQL
8+ instance.

## 11. Remaining configuration you need to provide

- Real MySQL credentials (or keep SQLite if traffic is low — it's fine for
  a small foundation site, just note it doesn't handle concurrent writers
  as well as MySQL under heavy load).
- Real SMTP credentials.
- A real `SECRET_KEY`.
- Your first admin's real name/email/password (`create_admin.py`).
- Real contact details in the footer (currently placeholders, unchanged
  from your original homepage).
- Events and Gallery pages were intentionally left as-is (out of scope per
  the brief) — the admin sidebar links to `/events` and `/gallery` as
  plain paths for when you build them.
#   s a m u n n a t i - f o u n d a t i o n  
 
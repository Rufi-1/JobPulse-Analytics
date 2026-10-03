# JobPulse Analytics

A full-stack Django job market platform with data-driven salary predictions,
personalized job recommendations, and an employer job-posting flow — built as a
learning/portfolio project. Runs entirely on SQLite, no external services or paid
APIs required.

## What it does

- **Job listings** — companies, categories, skills, salary ranges, remote/hybrid/onsite,
  experience levels, employment types, with search, multi-field filtering, and pagination.
- **Two account types, chosen at signup** — Job Seeker or Employer/Recruiter:
  - **Job seekers** build a profile (skills, desired role/location, expected salary),
    save jobs, apply with a resume upload and cover letter, track application status,
    and get personalized job recommendations.
  - **Employers** set up a company profile, then create/edit/activate/deactivate their
    own job postings, and review applicants per posting — reading each cover letter,
    downloading resumes, and updating status (Applied → Under Review → Interview →
    Offer/Rejected) from one screen.
- **Email notifications** — employers are emailed when a new application comes in;
  applicants are emailed when their status changes. Defaults to printing to the
  console (zero config); point it at real SMTP via environment variables whenever
  you want actual email.
- **Public, shareable profiles** — an optional read-only profile page
  (`/accounts/u/<username>/`) users can turn on and share a link to.
- **Market Insights dashboard** — Chart.js visualizations: jobs by category, top
  in-demand skills, jobs by location/experience/remote-type, average salary by
  category, and a 12-month salary trend line.
- **Salary Predictor** — a transparent, rule-based prediction engine that combines a
  baseline compensation model (experience level, location cost-of-living, skill
  premiums) with any historical market data on file, and shows its reasoning step by
  step instead of just spitting out a number.
- **My Market Position** — personalized analysis for logged-in job seekers: which
  in-demand skills for their desired role they have vs. are missing, and how their
  expected salary compares to what the engine predicts for their specific profile.
- **Company pages** — profiles, open roles, and user-submitted star ratings/reviews.
- **REST API** (Django REST Framework) — endpoints for jobs, companies, skills,
  categories, saved jobs, applications, reviews, profile, analytics trends, and a
  salary-prediction endpoint.
- **Customized Django admin**, SEO basics (sitemap, robots.txt, meta tags), custom
  404/500 pages, confirmation prompts on logout and other consequential actions, and
  a management command that seeds realistic sample data.
- **77 automated tests** across all three apps, covering models, views, permissions,
  the API, the prediction/recommendation engine, resume uploads, and email sending.

None of the prediction/recommendation logic uses an external AI service — it's all
plain, auditable Python in `analytics/engine.py`.

## Tech stack

- Django 5.x + Django REST Framework
- SQLite (zero config)
- Vanilla HTML/CSS/JS + Chart.js (via CDN) — no frontend build step

## Getting started

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r myproject/requirements.txt
cd myproject

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/`.

- Admin: `http://127.0.0.1:8000/admin/`
- API root: `http://127.0.0.1:8000/api/jobs/`

### Sample logins (from `seed_data`)

| Username          | Password        | Role                                       |
|-------------------|-----------------|---------------------------------------------|
| `alex_dev`        | `JobPulse2024!` | Job seeker (public profile enabled)          |
| `priya_data`      | `JobPulse2024!` | Job seeker                                   |
| `jamie_recruiter` | `JobPulse2024!` | Employer (already owns a company)            |

### Re-seeding

```bash
python manage.py seed_data --flush --jobs 200
```

## Running tests

```bash
python manage.py test
```

## Email notifications

By default, "sending" an email just prints it to the terminal — nothing to configure.
To send real email (e.g. via Gmail with an app password), set these before
`runserver`:

```cmd
set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set EMAIL_HOST=smtp.gmail.com
set EMAIL_PORT=587
set EMAIL_USE_TLS=True
set EMAIL_HOST_USER=you@gmail.com
set EMAIL_HOST_PASSWORD=your-16-character-app-password
set DEFAULT_FROM_EMAIL=you@gmail.com
```

## Project layout

```
myproject/
├── manage.py
├── requirements.txt
├── myproject/        # settings, root urls, wsgi/asgi
├── jobs/              # companies, categories, skills, postings, applications, reviews
├── accounts/           # user profiles, roles, auth
├── analytics/           # trends, salary predictor, recommendation engine
├── templates/            # all HTML templates
├── static/                 # css/js/img
└── media/                   # user uploads (avatars/logos/resumes)
```

## Notes

- Before pushing changes, make sure `SECRET_KEY` in `myproject/settings.py` isn't a
  value you've shared anywhere public — rotate it if in doubt:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- `DEBUG = True` and `ALLOWED_HOSTS = ['*']` in `settings.py` are meant for local use
  only — tighten both before deploying anywhere public.
- This project was built primarily as a demonstration/learning exercise, not as a
  production-ready job board — see `analytics/engine.py` for how the prediction and
  recommendation logic works under the hood.
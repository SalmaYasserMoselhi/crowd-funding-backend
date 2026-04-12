# CrowdFund Egypt — Backend

Django REST API for the CrowdFund Egypt platform.

## Tech Stack

- Python 3.12 / Django 6.0.4
- Django REST Framework + SimpleJWT
- PostgreSQL (Supabase)
- Supabase S3 (media storage)
- python-decouple (env config)

## Project Structure

```
apps/
  authentication/   # User registration, activation, JWT auth, profile
  projects/         # Projects, categories, tags, media
  social/           # Donations, comments, ratings, reports
  discovery/        # Homepage feed, search
config/
  settings/
    base.py         # Shared settings
    development.py  # Local dev overrides
    production.py   # Production overrides
core/               # Shared base classes and utilities
templates/emails/   # Activation and password reset emails
requirements/       # Split requirements (base / dev / prod)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt

cp .env.example .env
# fill in .env values

python manage.py migrate
python manage.py loaddata apps/projects/fixtures/categories.json
python manage.py runserver
```

## API Endpoints

| Prefix | App |
|---|---|
| `/api/auth/` | Authentication |
| `/api/projects/` | Projects, categories, tags |
| `/api/` | Donations, comments, ratings, reports |
| `/api/homepage/` | Homepage feed |

## Branch Rules

- All changes go through pull requests — direct push to `main` or `dev` is blocked.
- Feature branches: branch off `dev`, open PR into `dev`.
- Releases: PR from `dev` into `main`.

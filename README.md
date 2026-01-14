# LysAngels

Event marketplace connecting clients with service providers in Togo.

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python setup_togo.py
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000

## Stack

Django 6.0.1, Python 3.12, TailwindCSS, SQLite/PostgreSQL

## Structure

```
apps/
├── accounts/   - Users, authentication, admin
├── core/       - Base models (Country, City, Quartier)
├── vendors/    - Service providers
├── projects/   - Client projects
├── proposals/  - Quotes and proposals
└── messaging/  - Messaging system
```

## Settings

Development: `lysangels/settings/dev.py`  
Production: `lysangels/settings/prod.py`

## Key Commands

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py shell
python populate_database.py
```

## Production Notes

- Update SECRET_KEY
- Use PostgreSQL
- Configure ALLOWED_HOSTS
- Set up HTTPS
- Use Gunicorn + Nginx

---

January 2026

# Backend

## ECS

- Login: `ssh root@115.29.170.231`

## Start production(test run, unfinished lab1 setting)

1. Copy the `.api-keys` and `.env` files to `/Jobify/`
2. Set `DEBUG=False` in `backend/jobify_backend/settings.py`
3. `source .venv/bin/activate`
4. `python manage.py runserver`

## Django

Local superuser: `hollins`, password: `123`

```shell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## TODOs

- [ ] llama parse

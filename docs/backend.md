# Backend

## ECS

- Login: `ssh root@115.29.170.231`

## Start production(test run, unfinished lab1 setting)

1. Copy the `.api-keys` and `.env` files to `/Jobify/`
2. Set `DEBUG=False` in `backend/jobify_backend/settings.py`
3. `source .venv/bin/activate`
4. `python manage.py runserver`

## Testing

The testing configuration is under `pytest`.

```bash
cd Jobify/backend
pytest
```

### Testing fixtures

`tests/fixtures/generate_resume.py` generates realistic PDF resumes for various professions with random data.

## Django

Local superuser: `hollins`, password: `123`

```shell
# Migrate only when models have changed
python manage.py makemigrations
python manage.py migrate
python manage.py runserver > jobify.log 2>&1

sudo vi /etc/nginx/sites-available/jobify
sudo ln -s /etc/nginx/sites-available/jobify /etc/nginx/sites-enabled
```

## TODOs

- [ ] llama parse
- [ ] add login verification and redirection
- [ ] fix uv installation

## Llama parse

Read the [official python doc](https://docs.cloud.llamaindex.ai/llamaparse/getting_started?utm_source=chatgpt.com)

We are doing sync fetching for the api. We should limit the pdf file size uploaded(5MB).

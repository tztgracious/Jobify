# Backend

## Quick start

```bash
ssh root@115.29.170.231
cd Jobify
source .venv/bin/activate   # for django tests (python3.13)
source .apivenv/bin/activate    # for fastapi tests (python3.10)

# verify service status
curl -k https://115.29.170.231/ai/status
curl -k https://115.29.170.231/api/v1/debug/
```

## TODOs

- [x] llama parse
- [x] add login verification and redirection(deprecated)
- [x] fix uv installation
- [ ] interview questions
- [ ] interview feedbacks

## Django backend

Using `python3.13` at `Jobify/.venv`. Managed by `uv`.

Local superuser: `hollins`, password: `123`

```shell
# Migrate only when models have changed
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

### Testing

The testing configuration is under `pytest`.

```bash
cd Jobify/backend
pytest
pytest -vv
```

#### Testing fixtures

`tests/fixtures/generate_resume.py` generates realistic PDF resumes for various professions with random data.

## Fastapi

Using `python3.10` in `Jobify/.apivenv` for testing and local debugging.

## Llama parse

Read the [official python doc](https://docs.cloud.llamaindex.ai/llamaparse/getting_started?utm_source=chatgpt.com)

We are doing sync fetching for the api. We should limit the pdf file size uploaded(5MB).

## Reloading Services

| Action                                         | Reload Needed? | Service to Reload            |
| ---------------------------------------------- | -------------- | ---------------------------- |
| You change Python code (views, models, routes) | ✅             | Gunicorn (Django or FastAPI) |
| You change static files or templates           | ✅ (optional)  | Gunicorn                     |
| You change environment variables (.env)        | ✅             | Gunicorn                     |
| You change `nginx.conf` or site config         | ✅             | Nginx                        |
| You change SSL certificates or ports           | ✅             | Nginx                        |
| You edit systemd unit files                    | ✅             | Gunicorn + daemon-reload     |

```bash
#Reload Django
sudo systemctl restart gunicorn.service

# Reload fastapi
sudo systemctl restart fastapi.service

# Reload Nginx
sudo nginx -t     # ✅ Test config is valid
sudo systemctl reload nginx

# Or just restart it
sudo systemctl restart nginx
```

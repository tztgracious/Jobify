# Backend

## ECS

- Login: `ssh root@115.29.170.231`

## Start production

1. Copy the `.env` file to `/Jobify/`
2. Set `DEBUG=False` in `.env`
3. `source .venv/bin/activate`
4. `sudo systemctl restart gunicorn`

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
```

## TODOs

- [x] llama parse
- [x] add login verification and redirection(deprecated)
- [x] fix uv installation
- [ ] interview questions
- [ ] interview feedbacks

## Llama parse

Read the [official python doc](https://docs.cloud.llamaindex.ai/llamaparse/getting_started?utm_source=chatgpt.com)

We are doing sync fetching for the api. We should limit the pdf file size uploaded(5MB).

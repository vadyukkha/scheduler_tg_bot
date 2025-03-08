FROM python:3.11.11-slim

WORKDIR /project

RUN apt-get update \
    && apt-get clean \
    && pip install --no-cache-dir poetry poetry==2.0.1

COPY ./pyproject.toml ./poetry.lock ./README.md /project/

RUN poetry install --no-root

COPY app /project/app

ENV PYTHONPATH "${PYTHONPATH}:/project"

CMD ["bash", "-c", "poetry run python app/bot.py"] 

# python:3.12 (not 3.13): agency-swarm needs >=3.12, while ragleakguard's
# detection extra pins numpy<2 / spacy<3.8, which have no Python 3.13 wheels.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

COPY . .

# update as necessary in accordance with the security policy
USER root

CMD python -u main.py

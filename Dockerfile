FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/logs /app/staticfiles \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

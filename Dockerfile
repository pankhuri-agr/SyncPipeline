# 3.11 is sufficient

FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy requirements first so pip install is cached when only code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# start the execution
CMD ["python", "-m", "src.main"]
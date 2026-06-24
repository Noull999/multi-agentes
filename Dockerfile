# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

# Copy all 3 projects
COPY code-review-bot/ /app/code-review-bot/
COPY it-support-bot/ /app/it-support-bot/
COPY consultor-bot/ /app/consultor-bot/
COPY api/ /app/api/

# Create symlinks for the CLI launcher
RUN ln -sf /app/agente.sh /usr/local/bin/agentes

# Install dependencies for all projects
RUN for proj in code-review-bot it-support-bot consultor-bot; do \
        cd /app/$proj && pip install --no-cache-dir -r requirements.txt 2>&1 | tail -1; \
    done

# Install API dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# Cleanup
RUN rm -rf /root/.cache/pip

# Expose API port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

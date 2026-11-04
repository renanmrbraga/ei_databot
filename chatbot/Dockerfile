FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# A raiz é o contexto de build; o pacote chatbot.* deve estar em /app/chatbot.
COPY pyproject.toml README.md ./
COPY chatbot/ ./chatbot/
RUN python -m pip install --no-cache-dir .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "chatbot.chatbot:app", "--host", "0.0.0.0", "--port", "8000"]

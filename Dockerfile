FROM python:3.12-slim as requirements-stage
WORKDIR /tmp
RUN pip install poetry
RUN pip install poetry-plugin-export
COPY poetry.lock pyproject.toml /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
FROM python:3.12-slim
WORKDIR /app
COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY src/ /app/
EXPOSE 8080
CMD ["streamlit", "run", "ui/main.py", "--server.port=8080", "--server.address=0.0.0.0"]

FROM python:3.10-slim

WORKDIR /app

# Copy dependency lists
COPY pyproject.toml requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Copy app
COPY . .

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile
# Builds the Equo FastAPI application into an image

FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first - Docker caches this layer
# so it only reinstalls packages when requirements.txt changes
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
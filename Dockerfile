# Start from an official Python image (slim = minimal Linux + Python)
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies first (layer caching — only re-runs if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code
COPY . .

# Document the port the app runs on
EXPOSE 8000

# Start the API server (0.0.0.0 makes it accessible outside the container)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

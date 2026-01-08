# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a directory for the database volume
RUN mkdir /data

# Expose port 80
EXPOSE 80

# Run the application
CMD ["python", "app.py"]

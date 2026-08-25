# Use an official lightweight Python image
FROM python:3

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definitions (if you have them)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Command to run the script when the container starts
CMD ["python", "app.py"]
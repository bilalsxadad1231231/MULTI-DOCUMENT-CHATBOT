# Dockerfile (place in frontend folder)
FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit
EXPOSE 8501

# Command to run the applicatio
CMD ["streamlit", "run", "app.py"]

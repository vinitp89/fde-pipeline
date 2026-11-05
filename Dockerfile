# 1. Start with a lightweight Python base image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install required OS-level packages (like Postgres drivers)
RUN apt-get update && apt-get install -y libpq-dev gcc

# 4. Copy your requirements file and install Python dependencies
# (You will need a requirements.txt with pandas, requests, sqlalchemy, psycopg2)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your actual Python code into the container
COPY pipeline.py .

# 6. Command to run when the container starts
CMD ["python", "pipeline.py"]
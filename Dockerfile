# TODO
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose common ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Default command is a placeholder — replace with the actual start command for each service
CMD ["bash", "-c", "echo 'Container ready' && sleep infinity"]

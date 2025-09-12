FROM python:3.10-slim-buster

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose FastAPI (8080) and Streamlit (8501) ports
EXPOSE 8080 8501

# Run both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8080 & streamlit run app/app.py --server.port=8501 --server.address=0.0.0.0"]


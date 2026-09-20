FROM python:3.12-slim

# Set up non-root user for Hugging Face Spaces security standards
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /app

# Install dependencies
COPY --chown=user:user requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy application files
COPY --chown=user:user . /app

# Hugging Face Spaces exposes port 7860
EXPOSE 7860

# Start FastAPI web server on port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]

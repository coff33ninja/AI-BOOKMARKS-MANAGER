#!/bin/bash

echo "Setting up AI Bookmark Manager..."

# Ensure script exits on error
set -e

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Download spaCy model (if still used as a fallback or for other NLP tasks)
# If RoBERTa is the sole provider, this might be optional.
# The train_roberta.py script might not need it.
# python -m spacy download en_core_web_sm

# Train RoBERTa model
# This should ideally be done if the model doesn't exist or needs retraining.
# For a first run, or if data/custom_roberta_model is empty, this is crucial.
if [ ! -d "./data/custom_roberta_model" ] || [ -z "$(ls -A ./data/custom_roberta_model)" ]; then
  echo "Custom RoBERTa model not found or empty. Training model..."
  python backend/train_roberta.py
else
  echo "Custom RoBERTa model found. Skipping training."
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start PostgreSQL, backend, and frontend using Docker Compose
echo "Starting services with Docker Compose..."
docker-compose up --build -d # -d to run in detached mode

echo "Application should be starting up."
echo "Frontend will be available at http://localhost:3000 (or your Vite port)"
echo "Backend API will be available at http://localhost:8000"
echo "To see logs: docker-compose logs -f"
echo "To stop services: docker-compose down"

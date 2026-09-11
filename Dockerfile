# Stage 1: Build the Next.js frontend
FROM node:20-slim AS builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup the Python backend
FROM python:3.12-slim

WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy the built frontend static files from the builder stage
COPY --from=builder /app/frontend/out ./frontend/out

# Set environment variables
ENV PORT=8000
EXPOSE 8000

# Start the FastAPI server
CMD ["sh", "-c", "cd backend && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

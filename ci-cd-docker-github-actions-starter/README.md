
# CI/CD Pipeline with GitHub Actions & Docker (Starter)

This repository contains a minimal Flask web app, Dockerfile, Docker Compose file, unit tests, and a GitHub Actions workflow that:
1) Runs tests,
2) Builds a Docker image,
3) Pushes it to Docker Hub.


## Quick Start (Local)

Requirements:
- Docker Desktop (or Docker Engine)
- Git
- (Optional) Python if you want to run the app without Docker

### Run with Docker Compose
```bash
docker compose up --build -d
# open http://localhost:5000/
# health check:
curl http://localhost:5000/health
```

### Run without Docker (for development)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python app/app.py
```

## CI/CD via GitHub Actions

1. **Create a Docker Hub account** and a repository called `flask-ci-cd`.
2. **Create a Docker Hub access token** (Account Settings > Security > New Access Token).
3. **Create GitHub Secrets** in your repo:
   - `DOCKERHUB_USERNAME` = your Docker Hub username
   - `DOCKERHUB_TOKEN` = the access token you created
4. Push to `main` branch. The workflow will:
   - Run `pytest`
   - Build a Docker image
   - Push tags:
     - `YOUR_USERNAME/flask-ci-cd:latest`
     - `YOUR_USERNAME/flask-ci-cd:<git-sha>`

## Pull & Run the Image from Docker Hub
After a successful pipeline run:
```bash
docker pull YOUR_USERNAME/flask-ci-cd:latest
docker run -p 5000:5000 YOUR_USERNAME/flask-ci-cd:latest
```

## Endpoints
- `/` returns a hello message
- `/health` returns `{ "status": "ok" }`

## Repository Structure
```
.
├── .github/workflows/ci.yml
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
├── app/
│   └── app.py
├── docker-compose.yml
├── requirements-dev.txt
├── requirements.txt
└── tests/
    └── test_app.py
```

## Notes
- The Docker image uses **gunicorn** to serve the Flask app.
- For learning purposes we keep things minimal; in production you'd add logging, health probes, and proper config management.
"# Trigger workflow" 

# 🚀 CI/CD Monitoring Dashboard

A **containerized monitoring dashboard** built with **Flask, Gunicorn, and Docker**, deployed seamlessly on **Render Cloud**.  
This project provides **real-time visibility** into your CI/CD pipeline, server health, resource usage, Git metadata, and logs — all from a clean web interface.

---

## 📖 Overview
The dashboard is designed to **track and visualize CI/CD pipeline activity** in real time.  
It auto-refreshes every few seconds and exposes REST APIs to fetch live data about:
- **Pipeline Stages (Build, Test, Deploy)**
- **Server Uptime and Requests**
- **System Resource Usage (CPU, Memory)**
- **Container Info (ID, Ports, Uptime)**
- **Git Metadata (Branch, Commit, Author, Date)**
- **Recent Logs (latest 100+ requests)**

This makes it useful for **developers, DevOps engineers, and teams** who want an easy way to monitor their deployments.

---

## ✨ Features
- ✅ **Pipeline Status**: View Build/Test/Deploy results (via environment variables or CI updates).  
- ✅ **Server Health Monitoring**: Live uptime, request count, and server availability check.  
- ✅ **Resource Usage**: CPU & memory usage with short-term history charts (using `psutil`).  
- ✅ **Git Metadata Tracking**: Branch, commit hash, author, and commit date displayed.  
- ✅ **Container Insights**: Shows container ID, uptime, and mapped ports.  
- ✅ **Logs Panel**: Displays recent requests with timestamps & status codes.  
- ✅ **Dark Mode**: Toggle between light and dark UI.  
- ✅ **Auto Refresh**: Refreshes every 5s / 10s / 30s for live updates.  
- ✅ **REST APIs** (integrated for programmatic use).  

---

## 🛠️ Tech Stack
- **Backend**: Flask (Python) + Gunicorn  
- **Frontend**: HTML, CSS, Vanilla JS  
- **Containerization**: Docker  
- **Deployment**: Render (Free Tier Cloud Hosting)  
- **Monitoring**: psutil (system metrics)  

---

## 🏗️ Architecture
1. **Flask App** → Serves both the dashboard UI (`index.html`) and REST APIs.  
2. **Docker Container** → Ensures portability and consistent runtime environment.  
3. **Gunicorn** → Production-grade WSGI server for serving Flask.  
4. **Render Deployment** → Cloud service automatically builds & runs the container.  
5. **Auto-refreshing UI** → JS polls APIs (`/api/health`, `/api/stats`, etc.) every few seconds to keep the dashboard live.  

---

## 🔌 REST API Endpoints

| Endpoint        | Description |
|-----------------|-------------|
| `/api/health`   | Server uptime, requests served, CPU %, memory %, UTC time |
| `/api/stats`    | Resource usage with CPU/memory history |
| `/api/meta`     | Git branch, commit, author, pipeline stages, container info |
| `/api/logs`     | Recent request logs (path, status, timestamp) |
| `/health`       | Simple health check (returns `{status: "ok"}`) |

---

## ⚙️ Setup & Run Locally

1. **Clone the repository**
   ```powershell
   git clone https://github.com/Umarhuzaif/ci-cd-docker-github-actions-dashboard.git
   cd ci-cd-docker-github-actions-dashboard





#https://ci-cd-dashboard-z1wh.onrender.com/
# src/env.py
import os

WEB_SERVICE_BASE_URL = os.getenv("WEB_SERVICE_BASE_URL", "").rstrip("/")
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "")
REPORTS_DIR = os.getenv("REPORTS_DIR", "/tmp/reports")

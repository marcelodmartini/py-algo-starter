# src/uploader.py
import os
import requests
from .env import WEB_SERVICE_BASE_URL, UPLOAD_TOKEN


class UploadError(Exception):
    pass


def upload_report(report_path: str, target_name: str | None = None) -> str:
    """
    Sube report_path al Web Service (FastAPI) usando /upload-report.
    Devuelve la URL pública del reporte servido por el Web.
    """
    if not WEB_SERVICE_BASE_URL:
        raise UploadError("WEB_SERVICE_BASE_URL no configurada")
    if not UPLOAD_TOKEN:
        raise UploadError("UPLOAD_TOKEN no configurado")
    if not os.path.isfile(report_path):
        raise UploadError(f"No existe el archivo a subir: {report_path}")

    url = f"{WEB_SERVICE_BASE_URL}/upload-report"
    headers = {"X-Upload-Token": UPLOAD_TOKEN}
    files = {
        "file": (target_name or os.path.basename(report_path),
                 open(report_path, "rb"),
                 "text/html")
    }
    r = requests.post(url, headers=headers, files=files, timeout=60)
    r.raise_for_status()
    # el Web Service responde con JSON { "filename": ..., "url": ... }
    data = r.json()
    return data.get("url") or f"{WEB_SERVICE_BASE_URL}/report/{target_name or os.path.basename(report_path)}"

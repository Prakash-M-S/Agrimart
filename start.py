"""
One-Command Launcher for AgriMart AI
Starts the FastAPI backend server and automatically opens the application in your default browser.
Usage:
    python start.py
"""

import os
import socket
import threading
import time
import webbrowser

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def find_available_port(start_port: int = 8000) -> int:
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def open_browser_when_ready(url: str, delay: float = 1.2) -> None:
    time.sleep(delay)
    print(f"\n[AgriMart] Opening browser at: {url}\n")
    webbrowser.open(url)


def main() -> None:
    os.chdir(PROJECT_ROOT)
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    try:
        import uvicorn
        from app import app  # noqa: F401

        print("=" * 64)
        print(f" AgriMart AI Server starting at {url}")
        print(f" Interactive API Docs:          {url}/docs")
        print(" Press Ctrl+C to stop the server.")
        print("=" * 64)

        threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
        uvicorn.run("app:app", host="127.0.0.1", port=port, log_level="info")
    except ImportError:
        index_path = os.path.join(PROJECT_ROOT, "index.html")
        file_url = "file:///" + index_path.replace("\\", "/")
        print(f"[AgriMart] Uvicorn not found; opening standalone app directly: {file_url}")
        webbrowser.open(file_url)


if __name__ == "__main__":
    main()

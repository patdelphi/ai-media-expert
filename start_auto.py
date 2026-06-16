#!/usr/bin/env python3
"""AI Media Expert - startup supervisor.

Starts local development services in one console window:
- Backend API service (FastAPI + Uvicorn)
- Celery worker
- Frontend development server (React + Vite)
"""

import os
import sys
import time
import signal
import subprocess
import threading
import platform
import socket
import shutil
import webbrowser
from pathlib import Path
import logging
import json
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
LOGS_DIR = PROJECT_ROOT / "logs"


def print_flush(message: str = "") -> None:
    """Print with flush so batch-hosted output appears immediately."""
    print(message, flush=True)

class AutoServiceManager:
    """Service manager for non-interactive local startup."""
    
    def __init__(self):
        self.processes = {}
        self.log_handles = {}
        self.running = False
        self.redis_ready = False
        self.redis_started_by_script = False
        self.celery_enabled = False
        self.frontend_opened = False
        self.setup_logging()
    
    def setup_logging(self):
        """Create log directory."""
        LOGS_DIR.mkdir(exist_ok=True)
        print_flush(f"Log directory: {LOGS_DIR}")

    def print_runtime_summary(self) -> None:
        """Print current startup mode and feature availability."""
        startup_mode = "full" if self.redis_ready and self.celery_enabled else "degraded"
        queue_status = "enabled" if self.redis_ready and self.celery_enabled else "disabled"
        download_status = "enabled" if self.redis_ready and self.celery_enabled else "disabled"
        analysis_status = "enabled"

        print_flush("Runtime status:")
        print_flush(f"  - Mode:         {startup_mode}")
        print_flush(f"  - Redis:        {'enabled' if self.redis_ready else 'disabled'}")
        print_flush(f"  - Celery:       {'enabled' if self.celery_enabled else 'disabled'}")
        print_flush(f"  - Download:     {download_status}")
        print_flush(f"  - Queue tasks:  {queue_status}")
        print_flush(f"  - AI analysis:  {analysis_status}")
        print_flush()

    def try_open_frontend(self) -> None:
        """Open the frontend UI in the default browser once."""
        if self.frontend_opened:
            return
        try:
            webbrowser.open("http://localhost:5173")
            self.frontend_opened = True
            print_flush("OK: Opened frontend UI in the default browser.")
        except Exception as e:
            print_flush(f"WARN: Failed to open frontend UI automatically: {e}")
    
    def check_environment(self):
        """Check runtime environment."""
        print_flush("Checking environment...")
        
        if sys.version_info < (3, 9):
            print_flush(f"ERROR: Python version is too old: {sys.version}")
            print_flush("Please install Python 3.9+.")
            return False
        
        env_file = PROJECT_ROOT / ".env"
        if not env_file.exists():
            print_flush('ERROR: ".env" file was not found.')
            print_flush('Please copy ".env.example" to ".env" and configure it.')
            return False
        
        try:
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print_flush("ERROR: Node.js is not installed or unavailable.")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print_flush("ERROR: Node.js is not installed or unavailable.")
            return False
        
        print_flush("OK: Environment check passed.")
        return True
    
    def check_dependencies(self):
        """Check dependencies without auto-installing them."""
        print_flush("Checking dependencies...")

        try:
            result = subprocess.run(
                [sys.executable, "-c", "import fastapi, uvicorn, celery"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                print_flush("ERROR: Backend dependencies are missing.")
                print_flush("Please run: pip install -e .")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print_flush("ERROR: Failed to check backend dependencies.")
            return False

        if not (FRONTEND_DIR / "node_modules").exists():
            print_flush("ERROR: Frontend dependencies are missing.")
            print_flush('Please run "npm install" in "frontend".')
            return False

        print_flush("OK: Dependency check passed.")
        return True

    def is_tcp_port_open(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Return whether the TCP port is reachable."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def start_redis(self) -> bool:
        """Try to start Redis; degrade gracefully if unavailable."""
        print_flush("Starting Redis...")

        if self.is_tcp_port_open("127.0.0.1", 6379):
            print_flush("OK: Redis is already running on 127.0.0.1:6379.")
            self.redis_ready = True
            return True

        redis_server_path = os.environ.get("REDIS_SERVER_PATH")
        if redis_server_path:
            redis_executable = redis_server_path
        else:
            redis_executable = shutil.which("redis-server") or shutil.which("redis-server.exe")
            if not redis_executable and platform.system() == "Windows":
                candidates = [
                    r"C:\Program Files\Redis\redis-server.exe",
                    r"C:\Program Files (x86)\Redis\redis-server.exe",
                    r"C:\Redis\redis-server.exe",
                ]
                for candidate in candidates:
                    if Path(candidate).exists():
                        redis_executable = candidate
                        break

        if not redis_executable:
            print_flush("WARN: redis-server executable was not found. Redis/Celery will not start.")
            print_flush("      Download queue and async download features will be unavailable.")
            print_flush("      Video AI analysis main flow remains available.")
            self.redis_ready = False
            return False

        try:
            log_file = LOGS_DIR / "redis.log"
            log_handle = open(log_file, "w", encoding="utf-8")
            cmd = [
                redis_executable,
                "--port", "6379",
                "--save", "",
                "--appendonly", "no",
            ]
            process = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT,
            )
            self.processes["redis"] = process
            self.log_handles["redis"] = log_handle
            self.redis_started_by_script = True

            for _ in range(30):
                if self.is_tcp_port_open("127.0.0.1", 6379):
                    print_flush(f"OK: Redis started (PID: {process.pid}).")
                    print_flush(f"    Log file: {log_file}")
                    self.redis_ready = True
                    return True
                time.sleep(0.1)

            print_flush("WARN: Redis failed to start (port 6379 is not listening). Redis/Celery will not start.")
            print_flush(f"      Check log: {log_file}")
            print_flush("      Download queue and async download features will be unavailable.")
            print_flush("      Video AI analysis main flow remains available.")
            self.redis_ready = False
            return False
        except Exception as e:
            print_flush(f"WARN: Failed to start Redis: {e}")
            print_flush("      Redis/Celery will not start.")
            print_flush("      Download queue and async download features will be unavailable.")
            print_flush("      Video AI analysis main flow remains available.")
            self.redis_ready = False
            return False
    
    def init_database(self):
        """Initialize the database if needed."""
        print_flush("Initializing database...")
        
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from app.core.db_manager import ensure_database_ready
            
            if ensure_database_ready():
                print("OK: Database initialization completed.", flush=True)
                return True
            else:
                print_flush("ERROR: Database initialization failed.")
                return False
                
        except Exception as e:
            print_flush(f"ERROR: Database initialization error: {e}")
            logger.exception("Database initialization failed")
            return False
    
    def start_backend(self):
        """Start the backend API service."""
        print_flush("Starting backend API...")
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.app:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
            
            log_file = LOGS_DIR / "backend.log"
            log_handle = open(log_file, "w", encoding="utf-8")
            process = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT
            )
            
            self.processes['backend'] = process
            self.log_handles['backend'] = log_handle
            print_flush(f"OK: Backend API started (PID: {process.pid}).")
            print_flush("    URL: http://localhost:8000")
            print_flush(f"    Log file: {log_file}")
            
            return True
            
        except Exception as e:
            print_flush(f"ERROR: Failed to start backend API: {e}")
            return False
    
    def start_celery(self):
        """Start the Celery worker."""
        print_flush("Starting Celery worker...")

        if not self.redis_ready:
            print_flush("WARN: Redis is unavailable, skipping Celery startup.")
            return False
        
        try:
            cmd = [
                sys.executable, "-m", "celery",
                "-A", "app.tasks.celery",
                "worker",
                "--loglevel=info"
            ]
            
            log_file = LOGS_DIR / "celery.log"
            log_handle = open(log_file, "w", encoding="utf-8")
            process = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_ROOT
            )
            
            self.processes['celery'] = process
            self.log_handles['celery'] = log_handle
            self.celery_enabled = True
            print_flush(f"OK: Celery worker started (PID: {process.pid}).")
            print_flush(f"    Log file: {log_file}")
            
            return True
            
        except Exception as e:
            print_flush(f"ERROR: Failed to start Celery worker: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend development server."""
        print_flush("Starting frontend dev server...")
        
        try:
            if platform.system() == "Windows":
                cmd = ["npm.cmd", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
            else:
                cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
            
            log_file = LOGS_DIR / "frontend.log"
            log_handle = open(log_file, "w", encoding="utf-8")
            process = subprocess.Popen(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=FRONTEND_DIR,
                shell=False
            )
            
            self.processes['frontend'] = process
            self.log_handles['frontend'] = log_handle
            print_flush(f"OK: Frontend dev server started (PID: {process.pid}).")
            print_flush("    URL: http://localhost:5173")
            print_flush(f"    Log file: {log_file}")
            
            return True
            
        except Exception as e:
            print_flush(f"ERROR: Failed to start frontend dev server: {e}")
            return False
    
    def check_services_health(self):
        """Check service health after startup."""
        print_flush("Checking service health...")
        
        time.sleep(5)

        if self.redis_ready and self.is_tcp_port_open("127.0.0.1", 6379):
            print_flush("OK: Redis is healthy.")
        else:
            print_flush("WARN: Redis is not running. Celery-related features are unavailable.")
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print_flush("OK: Backend API is healthy.")
            else:
                print_flush("WARN: Backend API responded unexpectedly.")
        except requests.RequestException:
            print_flush("WARN: Backend API may still be starting.")
        
        try:
            response = requests.get("http://localhost:5173", timeout=5)
            if response.status_code == 200:
                print_flush("OK: Frontend dev server is healthy.")
                self.try_open_frontend()
            else:
                print_flush("WARN: Frontend dev server responded unexpectedly.")
        except requests.RequestException:
            print_flush("WARN: Frontend dev server may still be starting.")
    
    def monitor_processes(self):
        """Monitor process state while services are running."""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"WARN: {name} process exited (code: {process.returncode})", flush=True)
                    if process.returncode != 0:
                        print_flush(f"ERROR: {name} exited unexpectedly. Check its log file.")
            
            time.sleep(10)
    
    def stop_all(self):
        """Stop all managed services."""
        print_flush("\nStopping all services...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print_flush(f"  Stopping {name}...")
                process.terminate()
                
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print_flush(f"  Force killing {name}...")
                    process.kill()
                    process.wait()
                
                print_flush(f"  OK: {name} stopped.")
                
            except Exception as e:
                print_flush(f"  ERROR: Failed to stop {name}: {e}")
            finally:
                log_handle = self.log_handles.get(name)
                if log_handle:
                    try:
                        log_handle.close()
                    except Exception:
                        pass
        
        print_flush("All services stopped.")
    
    def start_all(self):
        """Start all local services with graceful degradation."""
        print_flush("=" * 50)
        print_flush("    AI Media Expert - Startup Supervisor")
        print_flush("=" * 50)
        print_flush()
        
        if not self.check_environment():
            return False
        
        if not self.check_dependencies():
            return False
        
        # Redis is optional. Main web application can still run without it.
        self.start_redis()

        if not self.init_database():
            return False
        
        print_flush("\nStarting services...")
        
        services = [
            ('backend', self.start_backend),
            ('frontend', self.start_frontend)
        ]
        if self.redis_ready:
            services.insert(1, ('celery', self.start_celery))
        
        success_count = 0
        for name, start_func in services:
            if start_func():
                success_count += 1
                time.sleep(2)
            else:
                print_flush(f"ERROR: Failed to start {name}.")
        
        if success_count == len(services):
            print_flush(f"\nOK: Started {success_count} services.")
            
            self.check_services_health()
            
            print_flush("\n" + "=" * 50)
            print_flush("            Services Started")
            print_flush("=" * 50)
            print_flush()
            print_flush("Service URLs:")
            print_flush(f"  - Redis:       {'redis://localhost:6379' if self.redis_ready else 'disabled'}")
            print_flush("  - Backend API: http://localhost:8000")
            print_flush("  - API Docs:    http://localhost:8000/docs")
            print_flush("  - Frontend UI: http://localhost:5173")
            print_flush("  - Admin Panel: http://localhost:8000/admin")
            print_flush()
            print_flush("Log files:")
            print_flush(f"  - Redis log:   {LOGS_DIR}/redis.log (if Redis was started by script)")
            print_flush(f"  - Backend log: {LOGS_DIR}/backend.log")
            print_flush(f"  - Celery log:  {LOGS_DIR}/celery.log (if Celery was started)")
            print_flush(f"  - Frontend log:{LOGS_DIR}/frontend.log")
            print_flush()
            print_flush("Notes:")
            print_flush("  - Keep this window open to keep services running.")
            print_flush("  - Press Ctrl+C to stop all services.")
            print_flush('  - Or run "stop_all_services.bat" to stop services.')
            print_flush()
            self.print_runtime_summary()
            
            self.running = True
            
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                self.stop_all()
            
            return True
        else:
            print_flush(f"\nERROR: Partial startup failure ({success_count}/{len(services)}).")
            self.stop_all()
            return False


def signal_handler(signum, frame):
    """Signal handler."""
    print_flush("\n\nStop signal received. Shutting down services...")
    sys.exit(0)


def main():
    """Program entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    manager = AutoServiceManager()
    
    try:
        success = manager.start_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print_flush(f"ERROR: Startup failed: {e}")
        logger.exception("Application startup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

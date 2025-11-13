"""
Streamlit application launcher utilities.

This module provides helper functions to launch the BTC Sentiment Analysis
dashboard and API server.

Usage:
    # Launch the Streamlit dashboard
    >>> from src.app import launch_dashboard
    >>> launch_dashboard()
    
    # Launch the FastAPI server
    >>> from src.app import launch_api
    >>> launch_api()
    
    # Or use the command-line:
    $ python -m src.app  # Launches dashboard
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def launch_dashboard(
    port: int = 8501,
    host: str = "localhost",
    headless: bool = False,
    open_browser: bool = True
) -> None:
    """
    Launch the Streamlit dashboard application.
    
    This function starts the Streamlit server running the BTC Sentiment
    Analysis dashboard. The dashboard must be able to connect to a running
    FastAPI backend (default: http://localhost:8000).
    
    Args:
        port: Port number for the Streamlit server (default: 8501)
        host: Host address to bind to (default: "localhost")
        headless: Run in headless mode without auto-opening browser (default: False)
        open_browser: Automatically open browser (default: True)
        
    Example:
        >>> # Launch dashboard on default port 8501
        >>> launch_dashboard()
        
        >>> # Launch on custom port without opening browser
        >>> launch_dashboard(port=8502, open_browser=False)
        
        >>> # Launch in headless mode for server deployment
        >>> launch_dashboard(headless=True, host="0.0.0.0")
    
    Raises:
        FileNotFoundError: If dashboard.py is not found
        RuntimeError: If Streamlit is not installed
    
    Note:
        - Ensure the FastAPI server is running before launching the dashboard
        - The dashboard expects the API at http://localhost:8000 by default
        - Press Ctrl+C to stop the dashboard server
    """
    # Get the dashboard script path
    app_dir = Path(__file__).parent
    dashboard_path = app_dir / "dashboard.py"
    
    if not dashboard_path.exists():
        raise FileNotFoundError(
            f"Dashboard script not found at {dashboard_path}\n"
            f"Expected: {dashboard_path.absolute()}"
        )
    
    # Build the streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        f"--server.port={port}",
        f"--server.address={host}",
    ]
    
    if headless:
        cmd.append("--server.headless=true")
    
    if not open_browser:
        cmd.append("--server.runOnSave=false")
        cmd.append("--browser.gatherUsageStats=false")
    
    # Set PYTHONPATH to include project root
    env = os.environ.copy()
    project_root = Path(__file__).parent.parent.parent
    env["PYTHONPATH"] = str(project_root)
    
    # Print launch info
    print("=" * 70)
    print("🚀 Launching BTC Sentiment Analysis Dashboard")
    print("=" * 70)
    print(f"Dashboard URL: http://{host}:{port}")
    print(f"Dashboard script: {dashboard_path}")
    print(f"Headless mode: {headless}")
    print(f"Auto-open browser: {open_browser}")
    print()
    print("📝 Note: Ensure FastAPI server is running at http://localhost:8000")
    print("         Start with: launch_api() or `uvicorn src.api.main:app`")
    print()
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 70)
    print()
    
    try:
        # Run streamlit
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped by user")
    except FileNotFoundError:
        raise RuntimeError(
            "Streamlit is not installed. Install it with: pip install streamlit"
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Dashboard failed with error code {e.returncode}")
        raise


def launch_api(
    port: int = 8000,
    host: str = "0.0.0.0",
    reload: bool = True,
    log_level: str = "info"
) -> None:
    """
    Launch the FastAPI backend server.
    
    This function starts the Uvicorn ASGI server running the BTC Sentiment
    Analysis API. The API provides endpoints for sentiment data and top drivers.
    
    Args:
        port: Port number for the API server (default: 8000)
        host: Host address to bind to (default: "0.0.0.0")
        reload: Enable auto-reload on code changes (default: True)
        log_level: Logging level - debug, info, warning, error (default: "info")
        
    Example:
        >>> # Launch API server on default port 8000
        >>> launch_api()
        
        >>> # Launch on custom port without auto-reload
        >>> launch_api(port=8080, reload=False)
        
        >>> # Launch with debug logging
        >>> launch_api(log_level="debug")
    
    Raises:
        RuntimeError: If Uvicorn is not installed
    
    Note:
        - API docs available at http://localhost:8000/docs
        - Health check at http://localhost:8000/api/v1/health/
        - Press Ctrl+C to stop the API server
    """
    # Build the uvicorn command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        f"--host={host}",
        f"--port={port}",
        f"--log-level={log_level}",
    ]
    
    if reload:
        cmd.append("--reload")
    
    # Set PYTHONPATH to include project root
    env = os.environ.copy()
    project_root = Path(__file__).parent.parent.parent
    env["PYTHONPATH"] = str(project_root)
    
    # Print launch info
    print("=" * 70)
    print("🚀 Launching BTC Sentiment Analysis API")
    print("=" * 70)
    print(f"API Base URL: http://{host}:{port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Health Check: http://localhost:{port}/api/v1/health/")
    print(f"Auto-reload: {reload}")
    print(f"Log level: {log_level}")
    print()
    print("📚 Available Endpoints:")
    print(f"   GET /api/v1/sentiment/?granularity=daily&days=30")
    print(f"   GET /api/v1/drivers/?day=YYYY-MM-DD")
    print(f"   GET /api/v1/health/")
    print()
    print("Press Ctrl+C to stop the API server")
    print("=" * 70)
    print()
    
    try:
        # Run uvicorn
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n\n✅ API server stopped by user")
    except FileNotFoundError:
        raise RuntimeError(
            "Uvicorn is not installed. Install it with: pip install uvicorn"
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ API server failed with error code {e.returncode}")
        raise


def main():
    """
    CLI entry point - launches the dashboard by default.
    
    Usage:
        python -m src.app          # Launch dashboard
        python -m src.app api      # Launch API server
    """
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        launch_api()
    else:
        launch_dashboard()


if __name__ == "__main__":
    main()


__all__ = [
    "launch_dashboard",
    "launch_api",
]

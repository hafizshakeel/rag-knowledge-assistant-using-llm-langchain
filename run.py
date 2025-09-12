#!/usr/bin/env python
"""
Main runner script to start the RAG application.
This will launch both the API server and the Streamlit UI.
"""
import os
import sys
import subprocess
import argparse
import time
import threading
import webbrowser
import signal
import queue
from core.utils.logger import get_logger

# Get application logger
logger = get_logger("runner")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create a stop event for signaling threads to exit
stop_event = threading.Event()

def stream_process_logs(process, prefix, stop_event):
    """Stream logs from a process with a given prefix"""
    while not stop_event.is_set() and process.poll() is None:
        line = process.stdout.readline()
        if line:
            logger.info(f"[{prefix}] {line.strip()}")
    
    # Read any remaining output
    for line in process.stdout:
        if line:
            logger.info(f"[{prefix}] {line.strip()}")

def start_backend(port=8080, debug=False):
    """Start the FastAPI backend server"""
    logger.info(f"Starting backend server on port {port}...")
    
    cmd = [
        sys.executable, 
        "-m", "uvicorn", 
        "api.main:app", 
        "--host", "0.0.0.0", 
        "--port", str(port)
    ]
    
    if debug:
        cmd.append("--reload")
    
    backend_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Start log streaming thread
    log_thread = threading.Thread(
        target=stream_process_logs,
        args=(backend_process, "API", stop_event)
    )
    log_thread.daemon = True
    log_thread.start()
    
    logger.info("Backend server started")
    return backend_process

def start_frontend(port=8501, debug=False):
    """Start the Streamlit frontend"""
    logger.info(f"Starting frontend on port {port}...")
    
    cmd = [
        sys.executable,
        "-m", "streamlit",
        "run", "app/app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0"
    ]
    
    if not debug:
        cmd.extend(["--server.headless", "true"])
    
    frontend_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Start log streaming thread
    log_thread = threading.Thread(
        target=stream_process_logs,
        args=(frontend_process, "UI", stop_event)
    )
    log_thread.daemon = True
    log_thread.start()
    
    logger.info("Frontend started")
    return frontend_process

def open_browser(port=8501, delay=2):
    """Open the web browser after a delay"""
    def _open_browser():
        time.sleep(delay)
        url = f"http://localhost:{port}"
        logger.info(f"Opening browser at {url}")
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="RAG Application Launcher")
    parser.add_argument("--backend-port", type=int, default=8080, help="Backend server port")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Frontend server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the frontend")
    parser.add_argument("--backend-only", action="store_true", help="Start only the backend")
    return parser.parse_args()

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "streamlit",
        "fastapi", 
        "uvicorn", 
        "langchain", 
        "langchain-openai", 
        "langchain-anthropic", 
        "langchain-groq", 
        "langchain-community", 
        "langchain-chroma", 
        "pydantic",
        "python-dotenv",
        "chromadb",
        "unstructured"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning("Missing required packages:")
        for package in missing_packages:
            logger.warning(f"  - {package}")
        
        install = input("Do you want to install them now? (y/n): ")
        if install.lower() == "y":
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            logger.info("All dependencies installed")
        else:
            logger.error("Please install the missing packages to run the application")
            sys.exit(1)
    else:
        logger.info("All dependencies are installed")

def print_header():
    """Print the application header"""
    header = """
    ╭────────────────────────────────────────────────╮
    │                                                │
    │          RAG Application Launcher              │
    │                                                │
    ╰────────────────────────────────────────────────╯
    """
    print(header)

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received. Stopping application...")
    stop_event.set()
    sys.exit(0)

def main():
    """Main function"""
    print_header()
    args = parse_args()
    
    # Check dependencies
    check_dependencies()
    
    # Set environment variable for debug mode
    if args.debug:
        os.environ["DEBUG"] = "True"
        logger.info("Debug mode enabled")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        backend_process = None
        frontend_process = None
        
        # Start backend if requested
        if not args.frontend_only:
            backend_process = start_backend(port=args.backend_port, debug=args.debug)
        
        # Give the backend server time to start
        if backend_process:
            time.sleep(2)
        
        # Start frontend if requested
        if not args.backend_only:
            frontend_process = start_frontend(port=args.frontend_port, debug=args.debug)
            
            # Open browser if not disabled
            if not args.no_browser:
                open_browser(port=args.frontend_port)
        
        # Print startup message
        print("\n" + "="*80)
        print(" RAG Assistant is starting up...")
        if backend_process:
            print(f" API server running at: http://localhost:{args.backend_port}")
        if frontend_process:
            print(f" Web UI available at: http://localhost:{args.frontend_port}")
        print("="*80 + "\n")
        
        # Keep the main thread alive and monitor processes
        while not stop_event.is_set():
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process and backend_process.poll() is not None:
                logger.error("Backend server stopped unexpectedly")
                stop_event.set()
                break
                
            if frontend_process and frontend_process.poll() is not None:
                logger.error("Frontend stopped unexpectedly")
                stop_event.set()
                break
            
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        stop_event.set()
        sys.exit(1)
    finally:
        # Set stop event to terminate log streaming threads
        stop_event.set()
        
        # Clean up processes
        if 'backend_process' in locals() and backend_process and backend_process.poll() is None:
            logger.info("Terminating backend process...")
            backend_process.terminate()
            backend_process.wait(timeout=5)
            
        if 'frontend_process' in locals() and frontend_process and frontend_process.poll() is None:
            logger.info("Terminating frontend process...")
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
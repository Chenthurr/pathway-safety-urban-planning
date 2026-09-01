#!/usr/bin/env python3
"""Cross-platform launcher for City Operations Center."""
import subprocess
import sys
import os
import time
import signal
import platform


def check_env():
    if "OPENAI_API_KEY" not in os.environ:
        print("⚠️  Warning: OPENAI_API_KEY not set!")
        print("   Set it with: export OPENAI_API_KEY=sk-your-key-here")
        sys.exit(1)


def start_services(mode="unified", api_port=8080, frontend_port=3000):
    print("🌆 Starting City Operations Center...")
    print(f"   Mode: {mode}")
    print(f"   API Port: {api_port}")
    print(f"   Frontend Port: {frontend_port}")
    print()

    # Start frontend server
    print("🖥️  Starting frontend dashboard...")
    frontend_cmd = [sys.executable, "-m", "http.server", str(frontend_port), "--directory", "frontend"]
    frontend_proc = subprocess.Popen(frontend_cmd)

    # Start backend
    print("🚀 Starting Pathway API server...")
    backend_cmd = [sys.executable, "src/main.py", "--mode", mode]
    backend_proc = subprocess.Popen(backend_cmd)

    print()
    print("✅ City Operations Center is running!")
    print(f"   Dashboard: http://localhost:{frontend_port}/dashboard.html")
    print(f"   API:       http://localhost:{api_port}")
    print(f"   Docs:      http://localhost:{api_port}/_schema")
    print()
    print("Press Ctrl+C to stop all services")

    def shutdown(signum, frame):
        print("\n🛑 Shutting down...")
        frontend_proc.terminate()
        backend_proc.terminate()
        time.sleep(1)
        frontend_proc.kill()
        backend_proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, shutdown)

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    check_env()
    mode = sys.argv[1] if len(sys.argv) > 1 else "unified"
    start_services(mode)

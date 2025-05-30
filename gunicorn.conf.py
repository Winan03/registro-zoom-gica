# gunicorn.conf.py
# Configuration file for Gunicorn to handle timeouts and memory issues

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Optimal worker count
worker_class = "sync"  # Use sync workers for CPU-intensive tasks
worker_connections = 1000

# Timeouts (CRITICAL for your issue)
timeout = 300  # 5 minutes instead of default 30 seconds
keepalive = 60
graceful_timeout = 300
worker_tmp_dir = "/dev/shm"  # Use memory for tmp files

# Memory management
max_requests = 100  # Restart workers after 100 requests
max_requests_jitter = 20  # Add randomness to prevent thundering herd
preload_app = True  # Load application before forking workers

# Logging
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "zoom_report_processor"

# Security
limit_request_line = 8190
limit_request_fields = 200
limit_request_field_size = 8190

# Environment
raw_env = [
    'PYTHONPATH=/opt/render/project/src',
]

# For Render.com specifically
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
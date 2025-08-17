# Gunicorn configuration for production
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Worker timeout - prevents hanging requests
keepalive = 30  # Keep-alive connections
max_requests = 1000  # Restart worker after N requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True  # Load app code before forking workers
enable_stdio_inheritance = True

# Graceful shutdowns
graceful_timeout = 30

def post_fork(server, worker):
    """Configure worker process after fork."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    
def worker_int(worker):
    """Handle worker interrupt signal."""
    worker.log.info("worker received INT or QUIT signal")
    
def pre_exec(server):
    """Pre-execution hook."""
    server.log.info("Forked child, re-executing.")
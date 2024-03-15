#!/bin/bash
gunicorn --workers=${WORKERS:-1} --threads ${THREADS:-3} --timeout 0 --bind :${PORT:-8000} --worker-class uvicorn.workers.UvicornWorker server:app
#!/bin/bash
gunicorn --workers=${WORKERS:-3} --threads ${THREADS:-3} --timeout 60 --bind :${PORT:-8000} --worker-class uvicorn.workers.UvicornWorker server:app
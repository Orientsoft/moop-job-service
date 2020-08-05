#! /bin/sh
celery -A job-service worker --loglevel=info
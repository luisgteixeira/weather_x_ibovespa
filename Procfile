web: gunicorn run:app
worker: celery -A projeto.celery worker -Q download -n worker-download -B --concurrency 1 --max-tasks-per-child=1
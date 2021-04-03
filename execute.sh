#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ⟳ ✔ ✘

main() {

    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Encerrando processos antigos \e[5m⟳\033[0m\r"
    pkill --signal 9 -f flower
    pkill --signal 9 -f celery
    pkill --signal 9 -f gunicorn
    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Encerrando processos antigos \e[32m✔\n\033[0m"

    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Configurando ambiente virtual \e[5m⟳\033[0m\r"
    pip --disable-pip-version-check install virtualenv | grep -v 'Requirement already'
   
    if [ ! -d "env" ]; then
        virtualenv -q env
    fi

    source .gotodata_env
    if [ "$1" == '--update' ]; then
        pip install --no-cache-dir --use-feature=2020-resolver -r requirements.txt | grep -v 'Requirement already'
    fi
    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Configurando ambiente virtual \e[32m✔\n\033[0m"

    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Iniciando aplicação \e[5m⟳\033[0m\r"
    nohup celery -A projeto.celery worker -Q download -n worker-download -B --concurrency 1 --max-tasks-per-child=1 --logfile=./logs/celery-download.log &> ./logs/celery-startup-download.log &
    nohup flower -A projeto.celery --address=0.0.0.0 --port=5555 --basic_auth=admin:1234goto &> ./logs/flower-startup.log &
    nohup gunicorn --bind=0.0.0.0:5001 --timeout 600 --workers=1 projeto:app --access-logfile ./logs/gunicorn-access.log --error-logfile ./logs/gunicorn-error.log --capture-output --log-level debug &> ./logs/gunicorn-startup.log &
    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Iniciando aplicação \e[32m✔\n\033[0m"

    return
}

main $1
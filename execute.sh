#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ⟳ ✔ ✘

main() {

    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Encerrando processos antigos \e[5m⟳\033[0m\r"
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
    nohup gunicorn --bind=0.0.0.0:5001 --timeout 600 --workers=1 projeto:app --access-logfile ./logs/gunicorn-access.log --error-logfile ./logs/gunicorn-error.log --capture-output --log-level debug &> ./logs/gunicorn-startup.log &
    echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Iniciando aplicação \e[32m✔\n\033[0m"

    return
}

main $1
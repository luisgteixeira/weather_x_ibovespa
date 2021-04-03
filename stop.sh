#!/usr/bin/env bash 
# -*- coding: utf-8 -*- 

echo -ne "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Encerrando aplicação \e[5m⟳\033[0m\r"
pkill --signal 9 -f flower
pkill --signal 9 -f celery
pkill --signal 9 -f execute.sh
pkill --signal 9 -f gunicorn
echo -ne  "\033[1m[`date +"%Y-%m-%d %T %z"`] [$$] Encerrando aplicação \e[32m✔\n\033[0m"
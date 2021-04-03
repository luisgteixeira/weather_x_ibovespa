#!/usr/bin/env bash 
# -*- coding: utf-8 -*- 

echo -ne '\033[1mConfigurando ambiente virtual   -----\033[0m'
source .gotodata_env
pip --disable-pip-version-check install virtualenv | grep -v 'Requirement already'

if [ ! -d "env" ]; then
    virtualenv -q env
fi

pip install --no-cache-dir --use-feature=2020-resolver -r requirements.txt | grep -v 'Requirement already'

echo -e '\033[1mConfigurando Banco de Dados  -----\033[0m'
flask db upgrade

echo -e '\033[1mConfigurando MongoDB  -----\033[0m'
sudo systemctl start mongod

# -*- coding: utf-8 -*-

import os, requests

from flask_migrate import Migrate
from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel

from pymongo import MongoClient
from bs4 import BeautifulSoup as bs

global climas
global ibovs

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION')
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}

babel = Babel(app)
@babel.localeselector
def get_locale():
    return 'pt_BR'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from projeto.model import *

@app.route('/')
def dashboard():

    global climas
    global ibovs

    registros = {}
    registros['ibovespa'] = ibovs.count_documents({})
    registros['clima'] = climas.count_documents({})

    ibovespa = list(ibovs.find().sort([('horario', -1)]).limit(5))
    clima = list(climas.find().sort([('horario', -1)]).limit(5))

    return render_template('index.html', registros=registros, ibovespa=ibovespa, clima=clima)


def get_info():

    # 10h às 17h dias úteis
    # ibovespa
    try:
        ibovespa = Ibovespa()

        url = 'https://www.infomoney.com.br/cotacoes/ibovespa/'
        session = requests.Session()
        site = session.get(url)
        bs_content = bs(site.content, 'html.parser')
        bs_content = bs_content.find('div', class_='line-info')

        ibovespa.pontos = int(bs_content.find('div', class_='value').find('p').string)
        ibovespa.variacao = float(bs_content.find('div', class_='percentage').find('p').string.strip().replace('%',''))
        ibovespa.id_unidade_variacao = 2
        ibovespa.minimo = int(bs_content.find('div', class_='minimo').find('p').string)
        ibovespa.maximo = int(bs_content.find('div', class_='maximo').find('p').string)
        ibovespa.volume = float(bs_content.find('div', class_='volume').find('p').string.replace('.','').replace(',','.'))

        db.session.add(ibovespa)
        db.session.flush()

        global ibovs
        ibovs.insert_one(ibovespa.to_json())

    except Exception as e:
        print("(LOG): EXCEÇÃO AO BAIXAR DADOS DO IBOVESPA:\n\t%s" % e)

    # clima
    urls = ['https://api.openweathermap.org/data/2.5/weather?id=' + c + '&appid=0a93da561b67da7eeae7499bd8eb6946&units=metric' for c in ['3448439', '3451190', '3469058', '3470127', '6322752', '3663517', '3452925', '3455775']]
        
    for url in urls:
        try:
            info = requests.get(url).json()
            clima = Clima()

            clima.cidade = info['name']
            clima.temperatura = float(info['main']['temp'])
            clima.id_unidade_temp = 1
            clima.umidade = info['main']['humidity']
            clima.id_unidade_umidade = 2
            clima.visibilidade = info['visibility'] / 1000
            clima.id_unidade_vis = 3
            clima.pressao = info['main']['pressure']
            clima.id_unidade_pressao = 4
            clima.ibovs.append(ibovespa)

            db.session.add(clima)
            db.session.flush()

            global climas
            climas.insert_one(clima.to_json())

        except Exception as e:
            print("(LOG): EXCEÇÃO AO BAIXAR DADOS DE CLIMA:\n\t%s" % e)

    db.session.commit()



@app.before_first_request
def first_request():

    cliente_mongo = MongoClient('mongodb://localhost:27017/')
    mongo_db = cliente_mongo['gotodata']

    global climas
    global ibovs
    climas = mongo_db.clima
    ibovs = mongo_db.ibovespa

    clima_ids = [i['id'] for i in list(climas.find({}, {'id':1, '_id':0}))]
    ibov_ids = [i['id'] for i in list(ibovs.find({}, {'id':1, '_id':0}))]

    clima = Clima.query.filter( ~Clima.id.in_(clima_ids) ).all()
    if len(clima) != 0:
        clima = [c.to_json() for c in clima]
        climas.insert_many(clima)

    ibovespa = Ibovespa.query.filter( ~Ibovespa.id.in_(ibov_ids) ).all()
    if len(ibovespa) != 0:
        ibovespa = [i.to_json() for i in ibovespa]
        ibovs.insert_many(ibovespa)

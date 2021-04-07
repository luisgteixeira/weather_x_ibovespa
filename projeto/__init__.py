# -*- coding: utf-8 -*-

# Flask
from flask_migrate import Migrate
from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel

# Utils
import os, requests, pytz
from datetime import datetime
from pymongo import MongoClient
from operator import itemgetter
from bs4 import BeautifulSoup as bs
from celery.schedules import crontab

timezone = pytz.timezone( os.getenv('TZ') )

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

# Celery
app.config.update(
    CELERY_BROKER_URL     = os.getenv('MONGODB_CONNECTION'),
    CELERY_RESULT_BACKEND = os.getenv('MONGODB_CONNECTION')
)

babel = Babel(app)
@babel.localeselector
def get_locale():
    return 'pt_BR'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
global mongo_db

# Interno
from projeto.model import *
from projeto.celery import *

celery = make_celery(app)
celery.conf.update(
    CELERYD_POOL_RESTARTS=True,
    CELERY_TIMEZONE=os.getenv('TZ')
)

@app.route('/')
def dashboard():

    global mongo_db
    atualiza_mongodb()

    try:
        registros = {}
        registros['ibovespa'] = mongo_db.ibovespa.count_documents({})
        registros['clima'] = mongo_db.clima.count_documents({})

        ibovespa = list(mongo_db.ibovespa.find().sort([('horario', -1)]).limit(5))
        clima = list(mongo_db.clima.find().sort([('horario', -1)]).limit(5))
    except:
        # caso haja problema com MongoDB, busca dados do Postgres
        ibovespa = [i.to_json() for i in Ibovespa.query.all()]
        ibovespa = sorted(ibovespa, key=itemgetter('id'), reverse=True)[0:6]

        clima = [c.to_json() for c in Clima.query.all()]
        clima = sorted(clima, key=itemgetter('id'), reverse=True)[0:6]

        registros = {}
        registros['ibovespa'] = len(ibovespa)
        registros['clima'] = len(clima)

    return render_template('index.html', registros=registros, ibovespa=ibovespa, clima=clima)


def atualiza_mongodb():

    try:
        global mongo_db

        # busca id's do mongodb e insere apenas aqueles que faltam
        clima_ids = [i['id'] for i in list(mongo_db.clima.find({}, {'id':1, '_id':0}))]
        ibov_ids = [i['id'] for i in list(mongo_db.ibovespa.find({}, {'id':1, '_id':0}))]

        clima = Clima.query.filter( ~Clima.id.in_(clima_ids) ).all()
        if len(clima) != 0:
            clima = [c.to_json() for c in clima]
            mongo_db.clima.insert_many(clima)

        ibovespa = Ibovespa.query.filter( ~Ibovespa.id.in_(ibov_ids) ).all()
        if len(ibovespa) != 0:
            ibovespa = [i.to_json() for i in ibovespa]
            mongo_db.ibovespa.insert_many(ibovespa)

        # remover do mongodb os registros que foram excluídos do PostgreSQL
        mongo_db.clima.remove({
            'id': {
                '$in': list(set(clima_ids) - set([c.id for c in Clima.query.all()]))
            }
        })

        # clima_ids = [c.id for c in Clima.query.all()]
        mongo_db.ibovespa.remove({
            'id': {
                '$in': list(set(ibov_ids) - set([i.id for i in Ibovespa.query.all()]))
            }
        })

    except Exception as e:
        print("(LOG): EXCEÇÃO AO ATUALIZAR DADOS NO MONGODB:\n\t%s" % e)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print('[LOG] Aplicando configuracao de horario')
    sender.add_periodic_task(crontab(minute = '*/30'), get_info.s(), queue='download')


@celery.task()
def get_info():

    print('[LOG] Baixando informacoes de Clima e da Ibovespa')
    global mongo_db

    # ibovespa
    try:
        ibovespa = Ibovespa()
        ultima_atualizacao = None
        urls = ['/', '/grafico', '/historico']
        i = 0

        while ultima_atualizacao is None and i < len(urls):
            url = 'https://www.infomoney.com.br/cotacoes/ibovespa' + urls[i]
            session = requests.Session()
            site = session.get(url)
            bs_content = bs(site.content, 'html.parser')

            ultima_atualizacao = bs_content.find('div', class_='date-update').find('span').string.split('\n')
            i += 1

        if ultima_atualizacao is None:
            return
        else:
            ultima_atualizacao = ultima_atualizacao[2].replace('às', '').strip() + ' ' + ultima_atualizacao[3].split('.')[0].strip()
        
        try:
            ultima_atualizacao = datetime.strptime(ultima_atualizacao, '%d/%m/%y %Hh%M')
        except:
            ultima_atualizacao = datetime.strptime(datetime.now(timezone).strftime('%d/%m/%y') + ' ' + ultima_atualizacao, '%d/%m/%y %Hh%M')

        ultima_atualizacao = ultima_atualizacao.replace(tzinfo=timezone)

        ultimo_inserido = Ibovespa.query.order_by(Ibovespa.id.desc()).first().horario
        ultimo_inserido = ultimo_inserido.replace(tzinfo=pytz.UTC)
        ultimo_inserido = ultimo_inserido.astimezone(timezone)

        if ultimo_inserido is None or ultima_atualizacao > ultimo_inserido:
            bs_content = bs_content.find('div', class_='line-info')

            ibovespa.pontos = int(bs_content.find('div', class_='value').find('p').string)
            ibovespa.variacao = float(bs_content.find('div', class_='percentage').find('p').string.strip().replace('%',''))
            ibovespa.id_unidade_variacao = 2
            ibovespa.minimo = int(bs_content.find('div', class_='minimo').find('p').string)
            ibovespa.maximo = int(bs_content.find('div', class_='maximo').find('p').string)
            ibovespa.volume = float(bs_content.find('div', class_='volume').find('p').string.replace('.','').replace(',','.'))

            db.session.add(ibovespa)
            db.session.flush()

            mongo_db.ibovespa.insert_one(ibovespa.to_json())
        else:
            print('[LOG] Ibovespa sem dados atualizados')
            print(f'\tultimo_inserido: {ultimo_inserido}')
            print(f'\tultima_atualizacao: {ultima_atualizacao}')
            return

    except Exception as e:
        print("(LOG): EXCEÇÃO AO BAIXAR DADOS DO IBOVESPA:\n\t%s" % e)

    # clima
    urls = ['https://api.openweathermap.org/data/2.5/weather?id=' + c + '&appid=' + os.getenv('API_KEY') + '&units=metric' for c in ['3448439', '3451190', '3469058', '3470127', '6322752', '3663517', '3452925', '3455775']]
        
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

            mongo_db.clima.insert_one(clima.to_json())

        except Exception as e:
            print("(LOG): EXCEÇÃO AO BAIXAR DADOS DE CLIMA:\n\t%s" % e)

    db.session.commit()


@app.before_first_request
def first_request():

    try:
        global mongo_db
        cliente_mongo = MongoClient(os.getenv('MONGODB_CONNECTION'))
        mongo_db = cliente_mongo['gotodata']

        atualiza_mongodb()
        celery.send_task('projeto.get_info', args=(), kwargs={}, queue='download')
    except Exception as e:
        print("(LOG): EXCEÇÃO AO CONECTAR MONGODB:\n\t%s" % e)

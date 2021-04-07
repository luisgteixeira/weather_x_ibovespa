import os, pytz

from sqlalchemy.schema import Sequence
from projeto import db, timezone

schema_name = os.getenv('DB_SCHEMA_NAME')

ibovespa_clima = db.Table(
    'ibovespa_clima',
    db.Column('id_clima', db.Integer(), db.ForeignKey(schema_name + '.clima.id')),
    db.Column('id_ibovespa', db.Integer(), db.ForeignKey(schema_name + '.ibovespa.id')),
    schema = schema_name
)
  
class Unidade(db.Model):
    __tablename__ = 'unidade'
    __table_args__ = {'schema': schema_name}
    id = db.Column(db.Integer, Sequence('unidade_id_seq', schema=schema_name), primary_key = True)
    medida = db.Column(db.String(10))
  
class Clima(db.Model):
    __tablename__ = 'clima'
    __table_args__ = {'schema': schema_name}
    id = db.Column(db.Integer, Sequence('clima_id_seq', schema=schema_name), primary_key = True)
    cidade = db.Column(db.String(40))
    temperatura = db.Column(db.Float)
    id_unidade_temp = db.Column(db.Integer(), db.ForeignKey(schema_name + '.unidade.id'))
    umidade = db.Column(db.Integer)
    id_unidade_umidade = db.Column(db.Integer(), db.ForeignKey(schema_name + '.unidade.id'))
    visibilidade = db.Column(db.Float)
    id_unidade_vis = db.Column(db.Integer(), db.ForeignKey(schema_name + '.unidade.id'))
    pressao = db.Column(db.Integer)
    id_unidade_pressao = db.Column(db.Integer(), db.ForeignKey(schema_name + '.unidade.id'))
    ibovs = db.relationship('Ibovespa', secondary = ibovespa_clima,
        backref = db.backref('clima', lazy = 'dynamic'))
    horario = db.Column(db.DateTime, default = db.func.current_timestamp())

    def to_json(self):
        return {
            'id':              self.id,
            'cidade':          self.cidade,
            'temperatura':     self.temperatura,
            'unidade_temp':    Unidade.query.get(self.id_unidade_temp).medida,
            'umidade':         self.umidade,
            'unidade_umidade': Unidade.query.get(self.id_unidade_umidade).medida,
            'visibilidade':    self.visibilidade,
            'unidade_vis':     Unidade.query.get(self.id_unidade_vis).medida,
            'pressao':         self.pressao,
            'unidade_pressao': Unidade.query.get(self.id_unidade_pressao).medida,
            'horario':         self.horario.replace(tzinfo=pytz.UTC).astimezone(timezone).strftime('%H:%M %d/%m/%Y')
        }

class Ibovespa(db.Model):
    __tablename__ = 'ibovespa'
    __table_args__ = {'schema': schema_name}
    id = db.Column(db.Integer, Sequence('ibovespa_id_seq', schema=schema_name), primary_key = True)
    pontos = db.Column(db.Integer)
    variacao = db.Column(db.Float)
    id_unidade_variacao = db.Column(db.Integer(), db.ForeignKey(schema_name + '.unidade.id'))
    minimo = db.Column(db.Integer)
    maximo = db.Column(db.Integer)
    volume = db.Column(db.Float)
    horario = db.Column(db.DateTime, default = db.func.current_timestamp())

    def to_json(self):
        return {
            'id':               self.id,
            'pontos':           self.pontos,
            'variacao':         self.variacao,
            'unidade_variacao': Unidade.query.get(self.id_unidade_variacao).medida,
            'minimo':           self.minimo,
            'maximo':           self.maximo,
            'volume':           self.volume,
            'horario':          self.horario.replace(tzinfo=pytz.UTC).astimezone(timezone).strftime('%H:%M %d/%m/%Y')
        }

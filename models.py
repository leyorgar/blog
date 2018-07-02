# 
from os import getenv
# Importamos FLASK
from flask import Flask
# Biblioteca que usa Flask para poder consultar la base de datos
from flask_sqlalchemy import SQLAlchemy
# Para ejecutar comandos de Flask
from flask_script import Manager
# Para que no toques la base de datos
from flask_migrate import Migrate, MigrateCommand
# Para tener numeros unicos
from uuid import uuid4
# Para informacion falsa
from faker import Faker
# Para encriptar contraseñas
from werkzeug.security import generate_password_hash
# Para numeros aleatorios
from random import randint
import random

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


class User(db.Model):
    '''
    Table user
    '''
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password = db.Column(db.String(106), nullable=False, unique=False)
    # Esta variable es para la confirmacion del email
    is_active = db.Column(db.Boolean)
    token = db.Column(db.String(32), nullable=False, unique=False)

    def __init__(self):
        self.is_active = False
        self.token = str(uuid4()).replace('-', '')

    def __repr__(self):
        return '<User %r>' % self.username
# Para relaciones n n de Tags con articulos 
tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True)
)        
class Articulos(db.Model):
    '''
    Table Articulos de blog
    '''
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    text = db.Column(db.Text, nullable=False)
    portada = db.Column(db.String(500), nullable=True)

    
    # Relación con usuario
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)
    user = db.relationship('User',
        backref=db.backref('articles', lazy=True))

    # Relación con categoría
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'),
        nullable=False)
    categoria = db.relationship('Categorias',
        backref=db.backref('articles', lazy=True))
    # Relacion con tag
    tags = db.relationship('Tag', secondary=tags, lazy='subquery',
        backref=db.backref('articles', lazy=True))


    def __repr__(self):
        return '<Article %r>' % self.title

class Categorias(db.Model):
    '''
    Table Categorias de los articulos
    '''
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

    def __repr__(self):
       return '<Categorias %r>' % self.name


class Tag(db.Model):
    '''
    Table Tags de los articulos
    '''
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

    def __repr__(self):
       return '<Tags %r>' % self.name

# Comandos

@manager.command
def init_data():
    # Recargar tablas
    db.drop_all()
    db.create_all()
    # Categorias
    CATEGORIAS_INICIALES = (
        'tiempo',
        'nacional',
        'internacional',
        'deportes',
        'entretenimiento'
        )
    for categoria in CATEGORIAS_INICIALES:
        my_new_category = Categorias(name=categoria)
        db.session.add(my_new_category)
    db.session.commit()
    print('CATEGORIAS creadas')

@manager.command
def fake_data():
    # Recargar tablas
    db.drop_all()
    db.create_all()

    # Creamos informacion falsa
    fake = Faker('es-ES')
    # Generamos los usuarios
    num_usuarios = 50
    for num in range(num_usuarios):
        temp_fake = fake.simple_profile()
        my_user = User()
        my_user.username = temp_fake['username']
        my_user.email = temp_fake['mail']
        my_user.password = generate_password_hash('123')
        my_user.is_active=True
        db.session.add(my_user)
    db.session.commit()
    print('Usuarios falsos creados')

    # Generamos categorias
    num_categorias = 10
    for num in range(num_categorias):
        my_categoria = Categorias()
        my_categoria.name = fake.word()
        db.session.add(my_categoria)
    db.session.commit()
    print('Categorias creadas')

    # Generamos Tags
    num_tags = 10
    for num in range(num_tags):
        my_tag = Tag()
        my_tag.name=fake.word()
        db.session.add(my_tag)
    db.session.commit()
    print('Tags creados')

    # Generamos Articulos
    num_articulos = 150
    for num in range(num_articulos):
        my_article = Articulos()
        my_article.title = fake.sentence()
        my_article.text = fake.text(max_nb_chars=10000)
        my_article.categoria_id = randint(1, num_categorias)
        my_article.user_id = randint(1, num_usuarios)
        # Creamos relaciones aleatrorias
        my_range = random.sample(range(1,10), 5)
        for tag_id in my_range:
            my_article.tags.append(Tag.query.get(tag_id))
        db.session.add(my_article)
    db.session.commit()
    print('Articulos creados')


if __name__ == '__main__':
    manager.run()
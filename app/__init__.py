from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from app.db import db
from flask_mail import Mail, Message
import secrets


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'seu-email@gmail.com'  # Substitua pelo seu e-mail
app.config['MAIL_PASSWORD'] = 'sua-senha'  # Substitua pela sua senha
app.config['MAIL_DEFAULT_SENDER'] = 'seu-email@gmail.com'  # O e-mail do remetente

mail = Mail(app)
db.init_app(app)


from app.models import Comentario
with app.app_context():
    db.create_all()
from app import routes

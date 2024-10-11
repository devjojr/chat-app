from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

socketio = SocketIO(app)


def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection


from app.routes import main
app.register_blueprint(main)

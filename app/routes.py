from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from flask_socketio import disconnect
from confluent_kafka import Producer, Consumer
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector
import json
from app import get_db_connection, socketio

main = Blueprint("main", __name__)

# track active users
active_users = []

producer = Producer({"bootstrap.servers": "localhost:9092"})


def message_to_kafka(message_data):
    try:
        message_to_bytes = json.dumps(message_data).encode("utf-8")
        producer.produce("chat-messages", value=message_to_bytes)
        producer.flush()
    except Exception as e:
        print(f"Error producing message: {str(e)}")


def user_auth(f):
    @wraps(f)
    def check_username(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return check_username


@main.route("/")
def index():
    if "username" in session:
        return redirect(url_for("main.chat"))
    return render_template("login.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                session["username"] = username
                return redirect(url_for("main.chat"))
            else:
                flash("Invalid username or password. Please try again.", "danger")
                return redirect(url_for("main.login"))

        except mysql.connector.Error as db_error:
            flash(f"Database error occurred. {str(db_error)}", "danger")
            return redirect(url_for("main.login"))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("main.login"))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    return render_template("login.html")


@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user_exist = cursor.fetchone()

            if user_exist:
                flash("Username already exists, please choose a different one.", "danger")
                return redirect(url_for("main.signup"))

            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            connection.commit()

            flash("Sign up successful! You can now log in.", "success")
            return redirect(url_for("main.login"))

        except mysql.connector.Error as db_error:
            flash(f"Database error occurred. {str(db_error)}", "danger")
            return redirect(url_for("main.signup"))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("main.signup"))

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    return render_template("signup.html")


@main.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


@main.route("/chat")
@user_auth
def chat():
    if "username" not in session:
        flash("You must be logged in to access the chat.", "danger")
        return redirect(url_for("main.index"))

    previous_messages = consume_message_history()

    return render_template("chat.html", username=session["username"], previous_messages=previous_messages)


@socketio.on("connect")
def handle_connect():
    if "username" not in session:
        disconnect()
    else:
        username = session["username"]
        if username not in active_users:
            active_users.append(username)
        print(f"{username} connected. Active users: {active_users}")

        message_history = consume_message_history()

        for message in message_history:
            socketio.emit("receive_message", message, to=request.sid)

        socketio.emit("active_users", active_users)


@socketio.on("send_message")
def handle_send_message(data):
    message = data["message"]
    username = session.get("username")

    message_data = {
        "username": username,
        "message": message
    }

    # sending message to kafka
    message_to_kafka(message_data)

    socketio.emit("receive_message", message_data)


@socketio.on("disconnect")
def handle_disconnect():
    if "username" in session:
        username = session["username"]
        if username in active_users:
            active_users.remove(username)
            print(f"{username} disconnected. Active user: {active_users}")
        socketio.emit("active_users", active_users)


def consume_message_history():
    consumer = get_kafka_consumer()

    previous_messages = []

    while True:
        message = consumer.poll(1.0)
        if message is None:
            break
        if message.error():
            print(f"Error retrieving messages: {message.error()}")
            continue
        message_value = json.loads(message.value().decode("utf-8"))
        previous_messages.append(message_value)

    consumer.close()
    return previous_messages


def get_kafka_consumer():
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'chat-consumer-group',
        'auto.offset.reset': 'earliest',
        "enable.auto.commit": True
    })
    consumer.subscribe(["chat-messages"])
    return consumer

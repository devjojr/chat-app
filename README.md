# Chat Application

This project is a real-time chat application built using Flask, WebSockets, Apache Kafka for messaging persistence, and MySQL for user authentication and management. Users can sign up, log in, join a chat room, and send real-time messages to each other. The app also features user presence tracking and message history retrieval.

## Features

- **User Authentication**: Users can sign up, log in, and log out.
- **Real-Time Messaging**: Messages are sent and received instantly between users using WebSockets.
- **Message Persistence**: Messages are stored in Apache Kafka and are persisted across sessions.
- **User List**: The active users in the chat are displayed and updated in real-time.
- **Message History**: Previously sent messages are loaded when a user logs in to the chat room.

## Setup Instructions

### Prerequisites

- **Python**
- **MySQL Server**
- **Apache Kafka**
- **Flask**

### Kafka Configuration

Make sure Kafka is installed and running. You'll need to:

1. **Start Zookeeper**

   ```bash
   bin/zookeeper-server-start.sh config/zookeeper.properties
   ```

2. **Start Kafka Broker**

   ```bash
   bin/kafka-server-start.sh config/server.properties
   ```

3. **Create Kafka Topic**

   ```bash
   bin/kafka-topics.sh --create --topic chat-messages --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --config retention.ms=3600000
   ```

### Set up MySQL Database

1. **Create a Database**

    ```sql
    CREATE DATABASE chat_app;
    USE chat_app;
    ```

2. **Create a users table**

   ```sql
   CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
   );
   ```

## Requirements

Create a virtual environment and install the required dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Environment Variables

   ```txt
   DB_HOST=localhost
   DB_USER=your_user_name
   DB_PASSWORD=your_db_password
   DB_NAME=chat_app
   ```

## How to Run

1. **Start Kafka**: Ensure Zookeeper and Kafka are running.
2. **Run the Flask Application**:

    ```bash
    python run.py
    ```

3. **Access the Application**: Open the browser and navigate to <http://localhost:5000/>

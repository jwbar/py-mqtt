from flask import Flask, render_template, jsonify
import threading
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# Flask app
app = Flask(__name__)

# MQTT configurations
MQTT_BROKER = "localhost"  # Change if broker is on another host
MQTT_PORT = 1883
MQTT_TOPICS = ["lasertag", "smartswitch", "test"]  # Add the topics you want to subscribe to

# Data structure to store messages by topic
messages = {topic: [] for topic in MQTT_TOPICS}
messages_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to all topics in the list
    for topic in MQTT_TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    # Append message to the respective topic
    payload = msg.payload.decode("utf-8")
    timestamp = datetime.now().isoformat()  # ISO 8601 format for timestamps

    with messages_lock:
        messages[msg.topic].append({
            "payload": payload,
            "client_id": client._client_id.decode("utf-8"),  # Extract client ID
            "timestamp": timestamp
        })
        # Keep only the last 50 messages per topic
        messages[msg.topic] = messages[msg.topic][-50:]

def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/messages")
def get_messages():
    with messages_lock:
        return jsonify(messages)

# Run the MQTT client in a separate thread
mqtt_client_thread = threading.Thread(target=mqtt_thread)
mqtt_client_thread.daemon = True
mqtt_client_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)

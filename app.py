import json
import os
from flask import Flask, request, render_template, jsonify
from cryptography.fernet import Fernet

app = Flask(__name__)

# Key file
key_file = "secret.key"

# Load or generate a new key
if os.path.exists(key_file):
    with open(key_file, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(key)

cipher_suite = Fernet(key)

# Initialize a JSON file to store chat messages
if not os.path.exists("messages.json"):
    with open("messages.json", "w") as f:
        json.dump([], f)

def read_messages():
    with open("messages.json", "r") as f:
        return json.load(f)

def write_message(data):
    messages = read_messages()
    
    # Encrypt the message before storing
    encrypted_message = cipher_suite.encrypt(data['text'].encode())
    
    # Store the message with username and encrypted text
    data['text'] = encrypted_message.decode()  # Store as string in JSON
    messages.append(data)
    
    with open("messages.json", "w") as f:
        json.dump(messages, f)

def decrypt_message(encrypted_message):
    return cipher_suite.decrypt(encrypted_message.encode()).decode()

@app.route('/')
def chat():
    """Render chat UI."""
    return render_template('chat.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    """API endpoint for sending a message."""
    data = request.json
    write_message(data)
    return jsonify({"status": "Message sent!"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    """API endpoint to fetch all messages."""
    messages = read_messages()
    # Decrypt messages before sending
    for msg in messages:
        try:
            msg['text'] = decrypt_message(msg['text'])
        except Exception as e:
            msg['text'] = "Error decrypting message"
            print(f"Decryption error: {e}")
    return jsonify(messages)

@app.route('/delete_message', methods=['POST'])
def delete_message():
    """API endpoint to delete a message by index."""
    data = request.json
    message_index = data.get("index")
    
    messages = read_messages()

    # Check if the index is valid
    if 0 <= message_index < len(messages):
        messages.pop(message_index)  # Remove the message from the list
        
        # Write the updated messages back to the file
        with open("messages.json", "w") as f:
            json.dump(messages, f)
        
        return jsonify({"status": "Message deleted!"}), 200
    else:
        return jsonify({"error": "Invalid message index!"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

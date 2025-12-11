from flask import Flask, render_template, jsonify
from flask_cors import CORS # <--- Check this line for typos!

# --- 1. INITIALIZATION ---
app = Flask(__name__)
CORS(app) 

# --- 2. MOCK DATA (Simulates a Database) ---
MOCK_CLIENTS_DATA = [
    {"id": 1, "name": "Alice Johnson", "status": "Active", "phone": "+14155552671"},
    {"id": 2, "name": "Bob Smith", "status": "Pending", "phone": "+14155552672"},
]

# --- 3. ROUTES (API Endpoints) ---

@app.route('/')
def home():
    """Renders the main HTML page (the app layout)."""
    return render_template('index.html')

@app.route('/api/clients')
def get_clients():
    """Returns the client data as JSON to the frontend."""
    return jsonify(MOCK_CLIENTS_DATA)
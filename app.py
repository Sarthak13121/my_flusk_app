from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Text

# --- 1. INITIALIZATION ---
app = Flask(__name__)
CORS(app) 

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. DATABASE MODELS ---

class Client(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    phone = Column(String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'phone': self.phone,
        }

class Task(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    due_date = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    assigned_to = Column(String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'due_date': self.due_date,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
        }

# --- 3. INITIAL DATABASE POPULATION ---

def initialize_database():
    """Creates tables and populates them with mock data if they don't exist."""
    with app.app_context():
        db.create_all() 

        if Client.query.count() == 0:
            initial_clients = [
                Client(name="Alice Johnson", status="Active", phone="+14155552671"),
                Client(name="Bob Smith", status="Pending", phone="+14155552672"),
            ]
            db.session.add_all(initial_clients)
            db.session.commit()

        if Task.query.count() == 0:
            initial_tasks = [
                Task(name="Send welcome package to Alice", due_date="2025-12-15", priority="High", assigned_to="User"),
                Task(name="Review Q4 earnings report", due_date="2025-12-20", priority="Medium", assigned_to="Admin"),
                Task(name="Follow up with Bob Smith", due_date="2025-12-13", priority="High", assigned_to="User"),
            ]
            db.session.add_all(initial_tasks)
            db.session.commit()
            
initialize_database()

# --- 4. ROUTES (API Endpoints - Client CRUD) ---

@app.route('/')
def home():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/api/clients', methods=['GET', 'POST'])
def handle_clients():
    # --- GET (READ ALL) ---
    if request.method == 'GET':
        clients = Client.query.all()
        clients_data = [client.to_dict() for client in clients]
        return jsonify(clients_data)

    # --- POST (CREATE) ---
    elif request.method == 'POST':
        data = request.json
        try:
            new_client = Client(
                name=data['name'],
                status=data.get('status', 'Active'),
                phone=data.get('phone', None)
            )
            db.session.add(new_client)
            db.session.commit()
            
            return jsonify({"status": "success", "client": new_client.to_dict()}), 201
        
        except Exception as e:
            print(f"Error creating client: {e}")
            return jsonify({"status": "error", "message": "Failed to create client"}), 400

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_client(client_id):
    """Handles GET, PUT, and DELETE requests for a single client."""
    client = Client.query.get_or_404(client_id)

    # --- GET (READ single client) ---
    if request.method == 'GET':
        return jsonify(client.to_dict())

    # --- PUT (UPDATE client) ---
    elif request.method == 'PUT':
        data = request.json
        try:
            client.name = data.get('name', client.name)
            client.status = data.get('status', client.status)
            client.phone = data.get('phone', client.phone)
            
            db.session.commit()
            return jsonify({"status": "success", "client": client.to_dict()}), 200
        except Exception as e:
            print(f"Error updating client: {e}")
            return jsonify({"status": "error", "message": "Failed to update client"}), 400

    # --- DELETE (DELETE client) ---
    elif request.method == 'DELETE':
        try:
            db.session.delete(client)
            db.session.commit()
            return jsonify({"status": "success", "message": "Client deleted"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to delete: {e}"}), 500

# --- 5. ROUTES (API Endpoints - Task CRUD) ---

@app.route('/api/tasks', methods=['GET', 'POST'])
def handle_tasks():
    # --- GET (READ ALL) ---
    if request.method == 'GET':
        tasks = Task.query.all()
        tasks_data = [task.to_dict() for task in tasks]
        return jsonify(tasks_data)

    # --- POST (CREATE) ---
    elif request.method == 'POST':
        data = request.json
        try:
            new_task = Task(
                name=data['name'],
                due_date=data.get('due_date', 'N/A'),
                priority=data.get('priority', 'Medium'),
                assigned_to=data.get('assigned_to', 'User')
            )
            db.session.add(new_task)
            db.session.commit()
            
            return jsonify({"status": "success", "task": new_task.to_dict()}), 201
        
        except Exception as e:
            print(f"Error creating task: {e}")
            return jsonify({"status": "error", "message": "Failed to create task"}), 400

@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_task(task_id):
    """Handles GET, PUT, and DELETE requests for a single task."""
    task = Task.query.get_or_404(task_id)

    # --- GET (READ single task) ---
    if request.method == 'GET':
        return jsonify(task.to_dict())

    # --- PUT (UPDATE task) ---
    elif request.method == 'PUT':
        data = request.json
        try:
            task.name = data.get('name', task.name)
            task.due_date = data.get('due_date', task.due_date)
            task.priority = data.get('priority', task.priority)
            task.assigned_to = data.get('assigned_to', task.assigned_to)
            
            db.session.commit()
            return jsonify({"status": "success", "task": task.to_dict()}), 200
        except Exception as e:
            print(f"Error updating task: {e}")
            return jsonify({"status": "error", "message": "Failed to update task"}), 400

    # --- DELETE (DELETE task) ---
    elif request.method == 'DELETE':
        try:
            db.session.delete(task)
            db.session.commit()
            return jsonify({"status": "success", "message": "Task deleted"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to delete: {e}"}), 500
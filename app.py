from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os 
import requests
import shutil 
from datetime import datetime 
from apscheduler.schedulers.background import BackgroundScheduler 

# --- NEW PDF IMPORTS ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io 
# --- END NEW PDF IMPORTS ---

# --- 1. INITIALIZATION ---
app = Flask(__name__)
CORS(app) 
app.config['SECRET_KEY'] = 'your_super_secret_key_here' # REQUIRED for Flask-Login sessions

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- WHATSAPP API CONFIGURATION (Secure Loading) ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'AC5db571bb528a49a6d02928f61d3f0a88') 
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'abfba41e43ab503891d7ab3e2744a485') 
WHATSAPP_SENDER = os.environ.get('WHATSAPP_SENDER', 'whatsapp:+14155238886')

# --- GLOBAL CONFIGURATION (E1 FIX) ---
# IMPORTANT: This must be a global variable accessible to the send_invoice_whatsapp function.
# You MUST replace this with your actual ngrok or production URL when testing file sending.
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', "https://ngrok.com/r/http-request")


db = SQLAlchemy(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database given their ID."""
    return User.query.get(int(user_id))

# --- 2. DATABASE MODELS ---
# (User, Client, Task, Invoice, LineItem classes remain unchanged)

class User(db.Model, UserMixin): 
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default='member') 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }

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

# --- NEW BILLING MODELS ---

class Invoice(db.Model):
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    issue_date = Column(String(50), nullable=False)
    due_date = Column(String(50))
    total_amount = Column(String(50), default='0.00')
    status = Column(String(20), default='Draft') 

    client_id = Column(Integer, ForeignKey('client.id'), nullable=False)
    client = relationship("Client", backref=db.backref('invoices', lazy=True))
    
    line_items = relationship("LineItem", backref='invoice', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'client_id': self.client_id,
            'client_name': self.client.name,
            'issue_date': self.issue_date,
            'due_date': self.due_date,
            'total_amount': self.total_amount,
            'status': self.status,
            'line_items': [item.to_dict() for item in self.line_items]
        }

class LineItem(db.Model):
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(String(50), nullable=False)
    subtotal = Column(String(50), nullable=False)

    invoice_id = Column(Integer, ForeignKey('invoice.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal
        }


# --- NEW FUNCTION: PDF GENERATION ---

def generate_invoice_pdf(invoice):
    """
    Generates a PDF file for a given Invoice object.
    Returns the path to the saved PDF file.
    """
    PDF_DIR = 'temp_invoices'
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        
    pdf_filename = f"invoice_{invoice.invoice_number}_{invoice.id}.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)

    # 1. Setup PDF Document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    # 2. Header and Client Info
    Story.append(Paragraph(f"<b>INVOICE #{invoice.invoice_number}</b>", styles['h1']))
    Story.append(Paragraph(f"<b>Client:</b> {invoice.client.name}", styles['Normal']))
    Story.append(Paragraph(f"<b>Issue Date:</b> {invoice.issue_date}", styles['Normal']))
    Story.append(Paragraph(f"<b>Due Date:</b> {invoice.due_date}", styles['Normal']))
    Story.append(Paragraph(f"<b>Total Due:</b> ${invoice.total_amount}", styles['h2']))
    Story.append(Paragraph("<br/>", styles['Normal']))

    # 3. Line Items Table Data
    table_data = [['Description', 'Qty', 'Unit Price', 'Subtotal']]
    
    for item in invoice.line_items:
        table_data.append([
            item.description,
            str(item.quantity),
            f"${item.unit_price}",
            f"${item.subtotal}"
        ])

    # Final Total Row
    table_data.append(['', '', '<b>TOTAL AMOUNT:</b>', f'<b>${invoice.total_amount}</b>'])

    # 4. Create and Style the Table
    table = Table(table_data, colWidths=[250, 50, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.yellow), # Highlight total row
    ]))

    Story.append(table)
    
    # 5. Build the PDF
    doc.build(Story)
    
    return pdf_path

# --- END PDF GENERATION FUNCTION ---


# --- 3. INITIAL DATABASE POPULATION ---

def initialize_database():
    """Creates tables and populates them with initial data."""
    with app.app_context():
        db.create_all() 
        # ... (unchanged initialization logic) ...
        if User.query.count() == 0:
            admin = User(username='admin', role='admin') 
            admin.set_password('12345') 
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: username='admin', password='12345'")

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
        

# --- 4. AUTHENTICATION AND MAIN ROUTES ---

@app.route('/register', methods=['POST'])
@login_required 
def register():
    # ... (register code) ...
    if current_user.role != 'admin':
        return jsonify({"status": "error", "message": "Permission denied. Only administrators can create new users."}), 403

    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": f"User '{username}' already exists"}), 409

    try:
        new_user = User(username=username)
        new_user.set_password(password) 
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": f"User '{username}' created successfully"
        }), 201
    
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({"status": "error", "message": "Failed to create user account"}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401
        
        login_user(user)
        return jsonify({"status": "success", "message": "Login successful"}), 200
        
    return render_template('login.html') 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login')) 

@app.route('/')
@login_required 
def home():
    """Renders the main HTML page and passes username for the header."""
    return render_template('index.html', username=current_user.username)

@app.route('/invoices') # <-- NEW INVOICE PAGE ROUTE
@login_required 
def invoices():
    """Renders the main invoices management page."""
    return render_template('invoices.html', username=current_user.username)


# --- NEW ROUTE: SERVE TEMPORARY INVOICE FILES ---
@app.route('/temp_invoices/<path:filename>')
@login_required 
def serve_invoice_file(filename):
    """
    Serves the generated PDF files from the temp_invoices directory.
    This route's path must match the PUBLIC_BASE_URL prefix used in send_invoice_whatsapp.
    """
    PDF_DIR = 'temp_invoices'
    
    try:
        return send_from_directory(
            PDF_DIR,
            filename,
            as_attachment=False, 
            mimetype='application/pdf'
        )
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Invoice file not found."}), 404

# --- 5. CLIENT CRUD ROUTES ---
# ... (Client routes remain the same) ...

@app.route('/api/clients', methods=['GET', 'POST'])
@login_required 
def handle_clients():
    if request.method == 'GET':
        clients = Client.query.all()
        clients_data = [client.to_dict() for client in clients]
        return jsonify(clients_data)

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
@login_required 
def handle_single_client(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'GET':
        return jsonify(client.to_dict())

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

    elif request.method == 'DELETE':
        try:
            db.session.delete(client)
            db.session.commit()
            return jsonify({"status": "success", "message": "Client deleted"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to delete: {e}"}), 500

# --- 6. TASK CRUD ROUTES ---

@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required 
def handle_tasks():
    if request.method == 'GET':
        tasks = Task.query.all()
        tasks_data = [task.to_dict() for task in tasks]
        return jsonify(tasks_data)

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
@login_required 
def handle_single_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == 'GET':
        return jsonify(task.to_dict())

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

    elif request.method == 'DELETE':
        try:
            db.session.delete(task)
            db.session.commit()
            return jsonify({"status": "success", "message": "Task deleted"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to delete: {e}"}), 500

# --- 7. INVOICE CRUD ROUTES ---

@app.route('/api/invoices', methods=['GET', 'POST'])
@login_required 
def handle_invoices():
    if request.method == 'GET':
        invoices = Invoice.query.all()
        invoices_data = [invoice.to_dict() for invoice in invoices]
        return jsonify(invoices_data)

    elif request.method == 'POST':
        data = request.json
        try:
            # 1. Calculate Total Amount from Line Items (Simple sum of subtotals)
            total_amount = 0.0
            line_items_data = data.get('line_items', [])
            
            for item in line_items_data:
                try:
                    total_amount += float(item['subtotal'])
                except (ValueError, KeyError):
                    return jsonify({"status": "error", "message": "Invalid or missing 'subtotal' in line items"}), 400

            # 2. Create the new Invoice object
            new_invoice = Invoice(
                invoice_number=data['invoice_number'],
                client_id=data['client_id'], 
                issue_date=data.get('issue_date', datetime.now().strftime("%Y-%m-%d")),
                due_date=data.get('due_date'),
                total_amount=f"{total_amount:.2f}",
                status=data.get('status', 'Draft')
            )
            db.session.add(new_invoice)
            db.session.commit() 

            # 3. Add Line Items
            for item_data in line_items_data:
                new_line_item = LineItem(
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    subtotal=item_data['subtotal'],
                    invoice_id=new_invoice.id 
                )
                db.session.add(new_line_item)
            
            db.session.commit()
            
            return jsonify({"status": "success", "invoice": new_invoice.to_dict()}), 201
        
        except Exception as e:
            print(f"Error creating invoice: {e}")
            return jsonify({"status": "error", "message": f"Failed to create invoice: {e}"}), 400

@app.route('/api/invoices/<int:invoice_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required 
def handle_single_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'GET':
        return jsonify(invoice.to_dict())

    elif request.method == 'DELETE':
        try:
            db.session.delete(invoice)
            db.session.commit()
            return jsonify({"status": "success", "message": "Invoice deleted"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to delete: {e}"}), 500
            
# --- 8. DASHBOARD STATISTICS ROUTE ---

@app.route('/api/stats', methods=['GET'])
@login_required 
def get_dashboard_stats():
    total_clients = Client.query.count()
    total_tasks = Task.query.count()
    pending_clients = Client.query.filter_by(status='Pending').count()
    high_priority_tasks = Task.query.filter_by(priority='High').count()
    total_invoices = Invoice.query.count()
    outstanding_invoices = Invoice.query.filter(Invoice.status.in_(['Draft', 'Sent'])).count()
    
    return jsonify({
        "total_clients": total_clients,
        "total_tasks": total_tasks,
        "pending_clients": pending_clients,
        "high_priority_tasks": high_priority_tasks,
        "total_invoices": total_invoices,
        "outstanding_invoices": outstanding_invoices
    })
    
# --- 9. WHATSAPP API INTEGRATION ROUTES ---

@app.route('/api/send_whatsapp', methods=['POST'])
@login_required 
def send_whatsapp_message():
    # IMPORTANT: Access secure tokens using os.environ.get()
    current_twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', TWILIO_ACCOUNT_SID)
    current_twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', TWILIO_AUTH_TOKEN)
    current_whatsapp_sender = os.environ.get('WHATSAPP_SENDER', WHATSAPP_SENDER)
    
    data = request.json
    recipient_phone = data.get('phone')
    message_body = data.get('message')

    if not recipient_phone or not message_body:
        return jsonify({"status": "error", "message": "Missing phone number or message body."}), 400

    if not recipient_phone.startswith('whatsapp:'):
        recipient_phone = f'whatsapp:{recipient_phone}'

    TWILIO_SMS_URL = f"https://api.twilio.com/2010-04-01/Accounts/{current_twilio_sid}/Messages.json"

    payload = {
        'To': recipient_phone,
        'From': current_whatsapp_sender,
        'Body': message_body,
    }

    try:
        response = requests.post(
            TWILIO_SMS_URL,
            data=payload,
            auth=(current_twilio_sid, current_twilio_token)
        )
        
        if response.status_code in [200, 201]:
            return jsonify({"status": "success", "message": "WhatsApp message successfully queued."}), 200
        else:
            print(f"Twilio Error Response: {response.text}")
            return jsonify({"status": "error", "message": f"Twilio API failed: {response.status_code}"}), 500

    except Exception as e:
        print(f"Network or API Call Exception: {e}")
        return jsonify({"status": "error", "message": "Failed to connect to WhatsApp service."}), 500


@app.route('/api/send_invoice/<int:invoice_id>', methods=['POST'])
@login_required 
def send_invoice_whatsapp(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Get client phone number 
    recipient_phone = invoice.client.phone
    if not recipient_phone:
        return jsonify({"status": "error", "message": f"Client {invoice.client.name} has no phone number recorded."}), 400
        
    # 1. Generate the PDF
    try:
        pdf_local_path = generate_invoice_pdf(invoice)
    except Exception as e:
        print(f"PDF GENERATION ERROR: {e}")
        return jsonify({"status": "error", "message": "Failed to generate invoice PDF."}), 500

    # 2. Get Twilio Credentials
    current_twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', TWILIO_ACCOUNT_SID)
    current_twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', TWILIO_AUTH_TOKEN)
    current_whatsapp_sender = os.environ.get('WHATSAPP_SENDER', WHATSAPP_SENDER)

    # 3. Create Public URL Placeholder
    # CRITICAL: This URL MUST be publicly accessible for Twilio to download the PDF.
    PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', "http://YOUR_NGROK_URL_OR_SERVER_IP") # <-- Using os.environ.get for security
    media_url = f"{PUBLIC_BASE_URL}/temp_invoices/{os.path.basename(pdf_local_path)}"

    TWILIO_SMS_URL = f"https://api.twilio.com/2010-04-01/Accounts/{current_twilio_sid}/Messages.json"

    # 4. Message payload (Uses MediaUrl for the PDF)
    payload = {
        'To': f'whatsapp:{recipient_phone}',
        'From': current_whatsapp_sender,
        'Body': f'Hello {invoice.client.name}, your Invoice #{invoice.invoice_number} for ${invoice.total_amount} is attached.',
        'MediaUrl': media_url, 
    }

    try:
        response = requests.post(
            TWILIO_SMS_URL,
            data=payload,
            auth=(current_twilio_sid, current_twilio_token)
        )
        
        if response.status_code in [200, 201]:
            invoice.status = 'Sent'
            db.session.commit()
            return jsonify({"status": "success", "message": f"Invoice {invoice.invoice_number} sent via WhatsApp."}), 200
        else:
            print(f"Twilio Error Response: {response.text}")
            return jsonify({"status": "error", "message": f"Twilio API failed: {response.status_code}"}), 500

    except Exception as e:
        print(f"Network or API Call Exception: {e}")
        return jsonify({"status": "error", "message": "Failed to connect to WhatsApp service."}), 500


# --- 10. DATABASE BACKUP AND MAINTENANCE FUNCTIONS ---

def backup_database():
    """
    Performs a safe backup of the SQLite database file.
    """
    BACKUP_DIR = 'backups'
    DATABASE_PATH = 'app.db'
    
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"app_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"--- DATABASE BACKUP SUCCESS: {backup_filename} ---")
    except Exception as e:
        print(f"!!! DATABASE BACKUP FAILED: {e} !!!")


def optimize_database():
    """
    Runs the SQLite VACUUM command to rebuild the database and free up unused space.
    """
    try:
        with app.app_context():
            db.session.execute(text('VACUUM;'))
            db.session.commit()
            print("--- DATABASE OPTIMIZATION (VACUUM) SUCCESSFUL ---")
    except Exception as e:
        print(f"!!! DATABASE OPTIMIZATION FAILED: {e} !!!")


def schedule_jobs():
    """Sets up the automatic scheduler for maintenance tasks."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(backup_database, 'cron', hour=2, minute=0, id='daily_backup')
    scheduler.add_job(optimize_database, 'cron', day_of_week='sun', hour=3, minute=0, id='weekly_optimization')
    scheduler.start()
    print("--- Background Scheduler Started ---")


# --- EXECUTION FLOW ---

initialize_database()

# Start the background tasks
with app.app_context(): 
    schedule_jobs()
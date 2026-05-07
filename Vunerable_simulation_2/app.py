# app.py — Vulnerable Flask App (Simulation 2)
import pickle, base64, subprocess
from flask import Flask, request, render_template_string

app = Flask(__name__)
SECRET = "hardcoded_secret_123"

@app.route('/dashboard')
def dashboard():
    user = request.args.get('user', 'guest')
    template = f"<h1>Welcome {user}</h1>"
    return render_template_string(template)   # Vuln 1

@app.route('/export')
def export():
    fmt = request.args.get('format', 'csv')
    filename = f"report_{fmt}.txt"
    subprocess.call(f"cat {filename}", shell=True)  # Vuln 2
    return "exported"

@app.route('/load_session', methods=['POST'])
def load_session():
    data = request.form.get('session')
    obj = pickle.loads(base64.b64decode(data))  # Vuln 3
    return str(obj)

@app.route('/ping')
def ping():
    host = request.args.get('host')
    result = subprocess.run(['ping', '-c', '1', host], capture_output=True)  # Vuln 4?
    return result.stdout
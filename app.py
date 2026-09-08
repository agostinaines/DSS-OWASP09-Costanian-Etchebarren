from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
app.secret_key = "p=CM37tcvsmx$oSI"

users = {
    'agos': '1234',
    'emilia': '1234',
    'demo': 'demo'
}

LOGIN_FAIL_COUNT = Counter(
    'app_login_failed_total', 
    'Total de intentos fallidos de inicio de sesión.', 
    ['method', 'endpoint']
)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            LOGIN_FAIL_COUNT.labels(
                    method=request.method, 
                    endpoint=request.path
                ).inc()
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
import logging
import os

from flask import Flask, render_template, request, redirect, url_for, session, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from werkzeug.exceptions import HTTPException

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s level=%(levelname)s logger=%(name)s %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

users = {
    os.environ['APP_USERNAME']: os.environ['APP_PASSWORD']
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
            logger.info(
                'event=login_success source_ip=%s',
                request.remote_addr or 'unknown'
            )
            return redirect(url_for('home'))
        else:
            LOGIN_FAIL_COUNT.labels(
                method=request.method,
                endpoint=request.path
            ).inc()
            logger.warning(
                'event=login_failure source_ip=%s',
                request.remote_addr or 'unknown'
            )
            return render_template('login.html', error='Usuario o contraseña incorrectos'), 401
    
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        logger.warning(
            'event=unauthorized_access endpoint=%s source_ip=%s',
            request.path,
            request.remote_addr or 'unknown'
        )
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/logout')
def logout():
    had_session = 'username' in session
    session.pop('username', None)
    logger.info(
        'event=logout authenticated_session=%s source_ip=%s',
        str(had_session).lower(),
        request.remote_addr or 'unknown'
    )
    return redirect(url_for('login'))

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        logger.warning(
            'event=http_error status=%s endpoint=%s source_ip=%s',
            error.code,
            request.path,
            request.remote_addr or 'unknown'
        )
        return error

    logger.exception(
        'event=unhandled_exception endpoint=%s source_ip=%s',
        request.path,
        request.remote_addr or 'unknown'
    )
    return 'Error interno del servidor', 500

if __name__ == '__main__':
    debug_enabled = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    logger.info(
        'event=application_start port=5000 debug=%s log_level=%s',
        str(debug_enabled).lower(),
        logging.getLevelName(logger.getEffectiveLevel())
    )
    app.run(host='0.0.0.0', port=5000, debug=debug_enabled)

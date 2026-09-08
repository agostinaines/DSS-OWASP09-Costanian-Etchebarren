from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "p=CM37tcvsmx$oSI"

users = {
    'agos': '1234',
    'emilia': '1234',
    'demo': 'demo'
}

error_counter = 0

def update_error_counter():
    global error_counter
    error_counter += 1

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
            update_error_counter()
            print(error_counter)
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
    app.run(host='0.0.0.0', port=80, debug=True)
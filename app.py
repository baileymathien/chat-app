from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)

# Model for Message
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(30), nullable=False)
    text = db.Column(db.String(200), nullable=False)

# Create database tables before the first request
@app.before_first_request
def create_tables():
    db.create_all()

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'Enter a username'
        elif not request.form['password']:
            error = 'Enter a password'
        elif User.query.filter_by(username=request.form['username']).first() != None:
            error = 'User already exists'
        elif request.form['password'] != request.form['password2']:
            error = 'The passwords do not match'
        else:
            username = request.form['username']
            password = request.form['password']
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('chat'))
    return render_template('register.html', error = error)

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    messages = Message.query.all()
    return render_template('chat.html', username=session['username'], messages=messages)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('message')
def handle_message(data):
    sender = session['username']
    new_message = Message(sender=sender, text=data)
    db.session.add(new_message)
    db.session.commit()
    socketio.emit('message', {'sender': sender, 'text': data})  # Remove 'broadcast=True'


if __name__ == '__main__':
    socketio.run(app, debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import flash

app = Flask(__name__)
app.secret_key = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

# ------------------ Models -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    priority = db.Column(db.String(20))
    tags = db.Column(db.String(100))
    due_date = db.Column(db.String(100))  # New: due date
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ------------------ Routes -------------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    filter_status = request.args.get('filter', 'all')
    query = Task.query.filter_by(user_id=session['user_id'])
    
    if filter_status == 'active':
        query = query.filter_by(completed=False)
    elif filter_status == 'completed':
        query = query.filter_by(completed=True)

    tasks = query.order_by(Task.id.desc()).all()
    return render_template('index.html', tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            flash("Login successful!", "success")  # ✅ Alert msg
            
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        user = User(username=request.form['username'], password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("User registered successfully!", "success")  # ✅ Alert msg
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' in session:
        new_task = Task(
            title=request.form['title'],
            priority=request.form['priority'],
            tags=request.form['tags'],
            due_date=request.form['due_date'],
            user_id=session['user_id']
        )
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.title = request.form['title']
        task.priority = request.form['priority']
        task.tags = request.form['tags']
        task.due_date = request.form['due_date']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', task=task)

@app.route('/complete/<int:id>')
def complete(id):
    task = Task.query.get(id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# ------------------ Main -------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

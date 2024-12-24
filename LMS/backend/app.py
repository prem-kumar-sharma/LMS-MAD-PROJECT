from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__, template_folder='../frontend/templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'user_login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.String(50))
    category = db.Column(db.String(50))
    enrollment_status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resources = db.relationship('Resource', backref='course', lazy=True, cascade='all, delete-orphan')
    batches = db.relationship('Batch', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    enrollments = db.relationship('Enrollment', backref='batch', lazy=True)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20))  # 'pdf' or 'video'
    file_path = db.Column(db.String(255))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'))
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin middleware
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('user_dashboard'))
        
        flash('Invalid username or password')
    return render_template('auth/login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, is_admin=True).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
            
        flash('Invalid admin credentials')
    return render_template('auth/admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('user_register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('user_login'))
        
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))

# Admin routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    courses = Course.query.all()
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/dashboard.html', courses=courses, users=users)

@app.route('/admin/courses/create', methods=['GET', 'POST'])
@admin_required
def admin_create_course():
    if request.method == 'POST':
        course = Course(
            name=request.form['name'],
            description=request.form['description'],
            duration=request.form['duration'],
            category=request.form['category'],
            enrollment_status=request.form['enrollment_status']
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_course.html')

@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.name = request.form['name']
        course.description = request.form['description']
        course.duration = request.form['duration']
        course.category = request.form['category']
        course.enrollment_status = request.form['enrollment_status']
        db.session.commit()
        flash('Course updated successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/courses/<int:course_id>/resources/add', methods=['POST'])
@admin_required
def admin_add_resource(course_id):
    if 'file' not in request.files:
        flash('No file provided')
        return redirect(url_for('admin_dashboard'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('admin_dashboard'))
        
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    resource = Resource(
        name=request.form['name'],
        type=request.form['type'],
        file_path=filename,
        course_id=course_id
    )
    db.session.add(resource)
    db.session.commit()
    
    flash('Resource added successfully')
    return redirect(url_for('admin_dashboard'))

# User routes
@app.route('/')
def home():
    courses = Course.query.filter_by(enrollment_status='Open').all()
    return render_template('courses/list.html', courses=courses)

@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    enrollments = current_user.enrollments
    return render_template('dashboard.html', enrollments=enrollments)

@app.route('/courses')
def course_list():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Course.query
    if search:
        query = query.filter(Course.name.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
        
    courses = query.all()
    return render_template('courses/list.html', courses=courses)

@app.route('/courses/<int:course_id>')
def course_view(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('courses/view.html', course=course)

@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def course_enroll(course_id):
    course = Course.query.get_or_404(course_id)
    batch_id = request.form.get('batch_id')
    
    if not batch_id:
        flash('Please select a batch')
        return redirect(url_for('course_view', course_id=course_id))
        
    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id,
        batch_id=batch_id
    )
    db.session.add(enrollment)
    db.session.commit()
    
    flash('Enrolled successfully')
    return redirect(url_for('user_dashboard'))

# Initialize database and create admin user
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, date, timedelta, time
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_migrate import Migrate
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure key in production
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.DateTime)
    gender = db.Column(db.String(20))
    health_conditions = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_doctor = db.Column(db.Boolean, default=False)
    is_patient = db.Column(db.Boolean, default=True)
    specialty = db.Column(db.String(100))
    availability_status = db.Column(db.String(50), default='Available')
    appointments = db.relationship('Appointment', backref='user', lazy=True, foreign_keys='Appointment.user_id')
    doctor_appointments = db.relationship('Appointment', backref='doctor', lazy=True, foreign_keys='Appointment.doctor_id')

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.full_name}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    health_problem = db.Column(db.String(200), nullable=False)
    symptoms = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    token_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Scheduled')  # Scheduled, Consulting, Completed
    notes = db.Column(db.Text, nullable=True)  # For doctor's notes
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# Forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()], render_kw={"placeholder": "YYYY-MM-DD"})
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    health_conditions = TextAreaField('Health Conditions', validators=[DataRequired()], render_kw={"placeholder": "e.g., Diabetes, Hypertension"})
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

HEALTH_PROBLEMS = [
    ('General Physician', 'General Physician'),
    ('Cold, Cough & Fever', 'Cold, Cough & Fever'),
    ('General Surgery', 'General Surgery'),
    ('Skin Problems', 'Skin Problems'),
    ('Cancer Advice', 'Cancer Advice'),
    ('Sexual Problems', 'Sexual Problems'),
    ("Women's Issues", "Women's Issues"),
    ('Acidity, Gas, Stomach Issues', 'Acidity, Gas, Stomach Issues'),
    ('Diabetic Consult', 'Diabetic Consult'),
    ('Orthopedics - Bones, Joints Issues', 'Orthopedics - Bones, Joints Issues'),
    ('Back & Joint Pains', 'Back & Joint Pains'),
    ('Ear, Nose & Throat', 'Ear, Nose & Throat'),
    ('Child/Infant Issues', 'Child/Infant Issues'),
    ('Conceiving Issues', 'Conceiving Issues'),
    ('Cardiology - Heart Related Issues', 'Cardiology - Heart Related Issues'),
    ('Breast Feeding Advice', 'Breast Feeding Advice'),
    ('Pulmonology', 'Pulmonology'),
    ('Ophthalmology', 'Ophthalmology'),
    ('Nephrology', 'Nephrology'),
    ('Lab Report Analysis', 'Lab Report Analysis'),
    ('Neurology', 'Neurology'),
    ('Hair and Scalp', 'Hair and Scalp'),
    ('Weight Management', 'Weight Management'),
    ('Pregnancy Problems', 'Pregnancy Problems'),
    ('Psychiatric Issues', 'Psychiatric Issues'),
    ('Psychological Counselling', 'Psychological Counselling'),
    ('Dentistry', 'Dentistry'),
    ('Endocrinology', 'Endocrinology'),
    ('Urology', 'Urology'),
    ("I don't know", "I don't know")  # Fixed line - changed single quotes to double quotes
]

HEALTH_PROBLEM_TO_SPECIALTY = {
    'General Physician': 'General',
    'Cold, Cough & Fever': 'General',
    'General Surgery': 'Surgeon',
    'Skin Problems': 'Dermatologist',
    'Cancer Advice': 'Oncologist',
    'Sexual Problems': 'Urologist',
    "Women's Issues": 'Gynecologist',
    'Acidity, Gas, Stomach Issues': 'Gastroenterologist',
    'Diabetic Consult': 'Endocrinologist',
    'Orthopedics - Bones, Joints Issues': 'Orthopedist',
    'Back & Joint Pains': 'Orthopedist',
    'Ear, Nose & Throat': 'ENT',
    'Child/Infant Issues': 'Pediatrician',
    'Conceiving Issues': 'Gynecologist',
    'Cardiology - Heart Related Issues': 'Cardiologist',
    'Breast Feeding Advice': 'Pediatrician',
    'Pulmonology': 'Pulmonologist',
    'Ophthalmology': 'Ophthalmologist',
    'Nephrology': 'Nephrologist',
    'Lab Report Analysis': 'General',
    'Neurology': 'Neurologist',
    'Hair and Scalp': 'Dermatologist',
    'Weight Management': 'Nutritionist',
    'Pregnancy Problems': 'Gynecologist',
    'Psychiatric Issues': 'Psychiatrist',
    'Psychological Counselling': 'Psychologist',
    'Dentistry': 'Dentist',
    'Endocrinology': 'Endocrinologist',
    'Urology': 'Urologist',
    "I don't know": 'General'  # Fixed line - changed single quotes to double quotes
}

class AppointmentForm(FlaskForm):
    health_problem = SelectField('Select Your Health Problem', choices=HEALTH_PROBLEMS, validators=[DataRequired()])
    symptoms = TextAreaField('Describe Your Symptoms', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Book Appointment')

    def __init__(self, min_date, max_date, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        self.min_date = min_date
        self.max_date = max_date

    def validate_date(self, field):
        if field.data is None:
            raise ValidationError('Please select a valid date.')
        if field.data < self.min_date:
            raise ValidationError(f'Date must be on or after {self.min_date.strftime("%Y-%m-%d")}.')
        if field.data > self.max_date:
            raise ValidationError(f'Date must be on or before {self.max_date.strftime("%Y-%m-%d")}.')

class AppointmentNotesForm(FlaskForm):
    notes = TextAreaField('Doctor Notes', validators=[DataRequired()])
    submit = SubmitField('Save Notes')

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        # Check for existing username or email
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'error')
            return render_template('register.html', form=form)

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            dob=datetime.combine(form.dob.data, time(0, 0), tzinfo=timezone.utc),
            gender=form.gender.data,
            health_conditions=form.health_conditions.data,
            is_admin=False,
            is_doctor=False,
            is_patient=True
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'error')
            print(f"Database error: {e}")  # Debugging
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            elif user.is_doctor:
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_doctor:
        return redirect(url_for('doctor_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))

@app.route('/patient_dashboard', methods=['GET', 'POST'])
@login_required
def patient_dashboard():
    if not current_user.is_patient:
        flash('Access denied. Patients only.', 'error')
        return redirect(url_for('home'))

    today = date.today()
    tomorrow = today + timedelta(days=1)
    one_month_later = today + relativedelta(months=1)

    form = AppointmentForm(min_date=tomorrow, max_date=one_month_later)
    form.date.render_kw = {
        "min": tomorrow.strftime('%Y-%m-%d'),
        "max": one_month_later.strftime('%Y-%m-%d'),
        "placeholder": f"Select a date between {tomorrow.strftime('%Y-%m-%d')} and {one_month_later.strftime('%Y-%m-%d')}"
    }

    if form.validate_on_submit():
        selected_date = form.date.data
        day_start = datetime.combine(selected_date, time(0, 0), tzinfo=timezone.utc)
        day_end = datetime.combine(selected_date, time(23, 59, 59), tzinfo=timezone.utc)

        # Check daily appointment limit
        daily_appointments = Appointment.query.filter(
            Appointment.date >= day_start,
            Appointment.date <= day_end
        ).count()
        if daily_appointments >= 100:
            flash('Daily appointment limit reached (100 patients). Please choose another date.', 'error')
            return render_template('patient_dashboard.html', form=form, user=current_user, appointments=[])

        # Assign doctor based on health problem
        health_problem = form.health_problem.data
        specialty = HEALTH_PROBLEM_TO_SPECIALTY.get(health_problem, 'General')
        doctor = User.query.filter_by(is_doctor=True, specialty=specialty, availability_status='Available').first()
        if not doctor:
            flash(f'No available doctors for {health_problem}. Please try another health problem or date.', 'error')
            return render_template('patient_dashboard.html', form=form, user=current_user, appointments=[])

        # Calculate token number and appointment time
        doctor_daily_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date >= day_start,
            Appointment.date <= day_end
        ).count()
        token_number = doctor_daily_appointments + 1
        avg_consultation_time = 15  # minutes
        start_time = datetime.combine(selected_date, time(9, 0), tzinfo=timezone.utc)
        appointment_time = start_time + timedelta(minutes=(token_number - 1) * avg_consultation_time)

        # Create appointment
        appointment = Appointment(
            user_id=current_user.id,
            doctor_id=doctor.id,
            health_problem=health_problem,
            symptoms=form.symptoms.data,
            date=appointment_time,
            token_number=token_number,
            status='Scheduled'
        )

        try:
            db.session.add(appointment)
            db.session.commit()
            flash(f'Appointment booked successfully! Token Number: {token_number}. Doctor: {doctor.full_name}. Please arrive at {appointment_time.strftime("%I:%M %p")}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'error')
            print(f"Database error: {e}")
        return redirect(url_for('patient_dashboard'))

    # Fetch appointments for display
    appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.asc()).all()
    appointments_data = []
    current_date = datetime.now(timezone.utc)
    for appointment in appointments:
        doctor = db.session.get(User, appointment.doctor_id)
        doctor_name = doctor.full_name if doctor else 'Unassigned'
        appointment_date = appointment.date if appointment.date.tzinfo else appointment.date.replace(tzinfo=timezone.utc)
        appointments_data.append({
            'appointment': appointment,
            'appointment_date': appointment_date,
            'doctor_name': doctor_name,
            'status': appointment.status
        })

    # Calculate age
    age = None
    if current_user.dob:
        age = (current_date - current_user.dob.replace(tzinfo=timezone.utc)).days // 365

    # Pass required data to template
    next_appointment = appointments_data[0]['appointment'] if appointments_data else None
    next_appointment_date = next_appointment.date if next_appointment else current_date + timedelta(days=30)
    days_in_month = (next_appointment_date.replace(day=28) + timedelta(days=4)).day
    start_day = next_appointment_date.replace(day=1).weekday()

    return render_template(
        'patient_dashboard.html',
        form=form,
        user=current_user,
        appointments_data=appointments_data,
        next_appointment=next_appointment,
        next_appointment_date=next_appointment_date,
        days_in_month=days_in_month,
        start_day=start_day,
        current_date=current_date,
        age=age  # Add age to the template context
    )
@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    # Today's appointments
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, time(0, 0), tzinfo=timezone.utc)
    day_end = datetime.combine(today, time(23, 59, 59), tzinfo=timezone.utc)
    
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).order_by(Appointment.token_number.asc()).all()
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date > day_end
    ).order_by(Appointment.date.asc()).all()
    
    # Format appointment data
    today_appointments_data = []
    for appointment in today_appointments:
        patient = db.session.get(User, appointment.user_id)
        today_appointments_data.append({
            'id': appointment.id,
            'token_number': appointment.token_number,
            'patient_name': patient.full_name if patient else 'Unknown',
            'health_problem': appointment.health_problem,
            'symptoms': appointment.symptoms,
            'time': appointment.date.strftime('%I:%M %p'),
            'status': appointment.status
        })
    
    upcoming_appointments_data = []
    for appointment in upcoming_appointments:
        patient = db.session.get(User, appointment.user_id)
        upcoming_appointments_data.append({
            'id': appointment.id,
            'token_number': appointment.token_number,
            'patient_name': patient.full_name if patient else 'Unknown',
            'health_problem': appointment.health_problem,
            'symptoms': appointment.symptoms,
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.date.strftime('%I:%M %p'),
            'status': appointment.status
        })
    
    return render_template(
        'doctor/doctor_dashboard.html',
        today_appointments=today_appointments_data,
        upcoming_appointments=upcoming_appointments_data
    )

@app.route('/appointment/<int:appointment_id>/start', methods=['POST'])
@login_required
def start_appointment(appointment_id):
    if not current_user.is_doctor:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment.status = 'Consulting'
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Appointment started'})

@app.route('/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
def complete_appointment(appointment_id):
    if not current_user.is_doctor:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment.status = 'Completed'
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Appointment completed'})

@app.route('/appointment/<int:appointment_id>/notes', methods=['GET', 'POST'])
@login_required
def appointment_notes(appointment_id):
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    form = AppointmentNotesForm()
    if form.validate_on_submit():
        appointment.notes = form.notes.data
        db.session.commit()
        flash('Notes saved successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))
    
    form.notes.data = appointment.notes  # Pre-fill existing notes
    
    # Get patient information
    patient = db.session.get(User, appointment.user_id)
    
    return render_template(
        'doctor/appointment_notes.html',
        form=form,
        appointment=appointment,
        patient=patient
    )

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('home'))
    
    # Today's appointments
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, time(0, 0), tzinfo=timezone.utc)
    day_end = datetime.combine(today, time(23, 59, 59), tzinfo=timezone.utc)
    
    today_appointments = Appointment.query.filter(
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).order_by(Appointment.date.asc()).all()
    
    # Summary statistics
    total_patients = User.query.filter_by(is_patient=True).count()
    total_doctors = User.query.filter_by(is_doctor=True).count()
    total_appointments = Appointment.query.count()
    scheduled_appointments = Appointment.query.filter_by(status='Scheduled').count()
    consulting_appointments = Appointment.query.filter_by(status='Consulting').count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()
    
    # Format appointment data
    today_appointments_data = []
    for appointment in today_appointments:
        patient = db.session.get(User, appointment.user_id)
        doctor = db.session.get(User, appointment.doctor_id)
        today_appointments_data.append({
            'id': appointment.id,
            'token_number': appointment.token_number,
            'patient_name': patient.full_name if patient else 'Unknown',
            'doctor_name': doctor.full_name if doctor else 'Unassigned',
            'health_problem': appointment.health_problem,
            'time': appointment.date.strftime('%I:%M %p'),
            'status': appointment.status
        })
    
    return render_template(
        'admin/dashboard.html',
        today_appointments=today_appointments_data,
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        scheduled_appointments=scheduled_appointments,
        consulting_appointments=consulting_appointments,
        completed_appointments=completed_appointments
    )

@app.route('/medicine_delivery', methods=['GET', 'POST'])
@login_required
def medicine_delivery():
    return render_template('medicine_delivery.html')

@app.route('/manage_labs', methods=['GET', 'POST'])
@login_required
def manage_labs():
    return render_template('manage_labs.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/covid_services')
def covid_services():
    return render_template('covid_services.html')

@app.route('/dental_care')
def dental_care():
    return render_template('dental_care.html')

# Database Initialization
def init_db():
    with app.app_context():
        db.drop_all()  # Clear existing data (for testing)
        db.create_all()
        # Add a test admin
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Admin User',
            is_admin=True,
            is_doctor=False,
            is_patient=False
        )
        admin.set_password('admin123')
        
        # Add test doctors with specialties
        doctor1 = User(
            username='doctor1',
            email='doctor1@example.com',
            full_name='Dr. John Doe',
            is_doctor=True,
            is_patient=False,
            specialty='General'
        )
        doctor1.set_password('doctor123')
        
        doctor2 = User(
            username='doctor2',
            email='doctor2@example.com',
            full_name='Dr. Jane Smith',
            is_doctor=True,
            is_patient=False,
            specialty='Dermatologist'
        )
        doctor2.set_password('doctor123')
        
        doctor3 = User(
            username='doctor3',
            email='doctor3@example.com',
            full_name='Dr. Mary Johnson',
            is_doctor=True,
            is_patient=False,
            specialty='Cardiologist'
        )
        doctor3.set_password('doctor123')
        
        # Add a test patient
        patient = User(
            username='patient1',
            email='patient1@example.com',
            full_name='Jane Doe',
            dob=datetime(1990, 1, 1, tzinfo=timezone.utc),
            gender='Female',
            health_conditions='Hypertension',
            is_patient=True
        )
        patient.set_password('patient123')
        
        db.session.add_all([admin, doctor1, doctor2, doctor3, patient])
        db.session.commit()
        print("Database initialized with test users: admin, doctor1-3, patient1")

if __name__ == '__main__':
    init_db()  # Initialize database on startup
    app.run(debug=True)
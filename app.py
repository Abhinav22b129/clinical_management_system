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
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a secure key in a real app
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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
    appointments = db.relationship('Appointment', backref='patient', lazy=True, foreign_keys='Appointment.user_id')
    doctor_appointments = db.relationship('Appointment', backref='doctor', lazy=True, foreign_keys='Appointment.doctor_id')

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

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
    status = db.Column(db.String(50), default='Scheduled')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    ("I don't know", "I don't know")
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
    "I don't know": 'General'
}

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

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists. Please use a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

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

class AddDoctorForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    specialty = SelectField('Specialty', choices=[
        ('General', 'General'),
        ('Dermatologist', 'Dermatologist'),
        ('Cardiologist', 'Cardiologist'),
        ('Surgeon', 'Surgeon'),
        ('Gynecologist', 'Gynecologist'),
        ('Pediatrician', 'Pediatrician'),
        ('Orthopedist', 'Orthopedist'),
        ('ENT', 'ENT'),
        ('Urologist', 'Urologist')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Doctor')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists. Please use a different one.')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            dob=datetime.combine(form.dob.data, time(0, 0),  # Removed tzinfo for simplicity
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
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        login_user(user, remember=True)
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    
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
    current_datetime = datetime.now()  # Removed timezone for simplicity

    form = AppointmentForm(min_date=tomorrow, max_date=one_month_later)
    form.date.render_kw = {
        "min": tomorrow.strftime('%Y-%m-%d'),
        "max": one_month_later.strftime('%Y-%m-%d'),
        "placeholder": f"Select between {tomorrow.strftime('%Y-%m-%d')} to {one_month_later.strftime('%Y-%m-%d')}"
    }

    if request.method == 'POST' and form.validate_on_submit():
        selected_date = form.date.data
        day_start = datetime.combine(selected_date, time(0, 0))
        day_end = datetime.combine(selected_date, time(23, 59, 59))

        daily_appointments = Appointment.query.filter(
            Appointment.date >= day_start,
            Appointment.date <= day_end
        ).count()
        
        if daily_appointments >= 100:
            flash('Daily appointment limit reached (100 patients). Please choose another date.', 'error')
            return redirect(url_for('patient_dashboard'))

        health_problem = form.health_problem.data
        specialty = HEALTH_PROBLEM_TO_SPECIALTY.get(health_problem, 'General')
        doctor = User.query.filter(
            User.is_doctor == True,
            User.specialty == specialty,
            User.availability_status == 'Available'
        ).first()
        
        if not doctor:
            flash(f'No available doctors for {health_problem}. Please try another health problem or date.', 'error')
            return redirect(url_for('patient_dashboard'))

        doctor_daily_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date >= day_start,
            Appointment.date <= day_end
        ).count()
        
        token_number = doctor_daily_appointments + 1
        avg_consultation_time = 15
        start_time = datetime.combine(selected_date, time(9, 0))
        appointment_time = start_time + timedelta(minutes=(token_number - 1) * avg_consultation_time)

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
            flash(
                f'Appointment booked successfully! Token: {token_number}. '
                f'Doctor: Dr. {doctor.full_name}. '
                f'Time: {appointment_time.strftime("%Y-%m-%d %I:%M %p")}',
                'success'
            )
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'error')
        
        return redirect(url_for('patient_dashboard'))

    appointments = Appointment.query.filter(
        Appointment.user_id == current_user.id,
        Appointment.date >= current_datetime
    ).order_by(Appointment.date.asc()).all()

    appointments_data = []
    for appointment in appointments:
        doctor = db.session.get(User, appointment.doctor_id)
        appointments_data.append({
            'appointment': appointment,
            'doctor_name': doctor.full_name if doctor else 'Unassigned',
            'status': appointment.status
        })

    age = None
    if current_user.dob:
        age = (current_datetime - current_user.dob).days // 365

    return render_template(
        'patient_dashboard.html',
        form=form,
        user=current_user,
        appointments_data=appointments_data,
        current_date=current_datetime,
        age=age,
        today=today
    )

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    today = datetime.now().date()
    day_start = datetime.combine(today, time(0, 0))
    day_end = datetime.combine(today, time(23, 59, 59))
    
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).order_by(Appointment.date.asc()).all()
    
    todays_appointments_data = []
    for appointment in today_appointments:
        patient = db.session.get(User, appointment.user_id)
        todays_appointments_data.append({
            'appointment': appointment,
            'patient_name': patient.full_name if patient else 'Unknown',
            'patient_initials': ''.join([name[0] for name in patient.full_name.split()[:2]]).upper() if patient else '?',
            'health_problem': appointment.health_problem,
            'symptoms': appointment.symptoms,
            'token_number': appointment.token_number
        })
    
    return render_template(
        'doctor/doctor_dashboard.html',
        doctor_name=current_user.full_name,
        doctor_initials=''.join([name[0] for name in current_user.full_name.split()[:2]]).upper(),
        todays_appointments=len(todays_appointments_data),
        todays_appointments_data=todays_appointments_data,
        total_patients=len({a.user_id for a in Appointment.query.filter_by(doctor_id=current_user.id).all()}),
        monthly_revenue=0,
        average_rating=5.0,
        recent_patients=[]
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

@app.route('/appointment/<int:appointment_id>/confirm', methods=['POST'])
@login_required
def confirm_appointment(appointment_id):
    if not current_user.is_doctor:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment.status = 'Confirmed'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Appointment confirmed'})

@app.route('/appointment/<int:appointment_id>/no_show', methods=['POST'])
@login_required
def mark_no_show(appointment_id):
    if not current_user.is_doctor:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    if appointment.status not in ['Scheduled', 'Confirmed']:
        return jsonify({'status': 'error', 'message': 'Cannot mark this appointment as no-show'}), 400
    
    appointment.status = 'No-Show'
    appointment.notes = appointment.notes + f"\n[Marked as No-Show by Dr. {current_user.full_name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]" if appointment.notes else f"[Marked as No-Show by Dr. {current_user.full_name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Appointment marked as no-show'})

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('home'))
    
    today = datetime.now().date()
    day_start = datetime.combine(today, time(0, 0))
    day_end = datetime.combine(today, time(23, 59, 59))
    
    today_appointments = Appointment.query.filter(
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).order_by(Appointment.date.asc()).all()
    
    total_patients = User.query.filter_by(is_patient=True).count()
    total_doctors = User.query.filter_by(is_doctor=True).count()
    total_appointments = Appointment.query.count()
    
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
        total_appointments=total_appointments
    )

@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('home'))
    
    form = AddDoctorForm()
    if form.validate_on_submit():
        doctor = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            is_doctor=True,
            is_patient=False,
            is_admin=False,
            specialty=form.specialty.data
        )
        doctor.set_password(form.password.data)
        
        try:
            db.session.add(doctor)
            db.session.commit()
            flash(f'Doctor {form.full_name.data} added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding doctor: {str(e)}', 'error')
    
    return render_template('admin/add_doctor.html', form=form)

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Admin User',
            is_admin=True,
            is_patient=False,
            is_doctor=False
        )
        admin.set_password('admin123')
        
        doctor = User(
            username='doctor1',
            email='doctor1@example.com',
            full_name='Dr. John Doe',
            is_doctor=True,
            is_patient=False,
            is_admin=False,
            specialty='General'
        )
        doctor.set_password('doctor123')
        
        patient = User(
            username='patient1',
            email='patient1@example.com',
            full_name='Jane Doe',
            is_patient=True,
            is_admin=False,
            is_doctor=False,
            dob=datetime(1990, 1, 1),
            gender='Female',
            health_conditions='Hypertension'
        )
        patient.set_password('patient123')
        
        db.session.add_all([admin, doctor, patient])
        db.session.commit()
        print("Database initialized with test users: admin, doctor1, patient1")

if __name__ == '__main__':
    # Uncomment the next line for the first run to initialize the database, then comment it out
    # init_db()
    app.run(debug=True)
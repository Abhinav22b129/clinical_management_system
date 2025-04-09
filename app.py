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

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['TEMPLATES_AUTO_RELOAD'] = True
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
    status = db.Column(db.String(50), default='Scheduled')
    notes = db.Column(db.Text, nullable=True)
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

@app.route('/')
def home():
    print("Rendering home.html")
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'error')
            return render_template('register.html', form=form)

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
            print(f"Database error: {e}")
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

        daily_appointments = Appointment.query.filter(
            Appointment.date >= day_start,
            Appointment.date <= day_end
        ).count()
        if daily_appointments >= 100:
            flash('Daily appointment limit reached (100 patients). Please choose another date.', 'error')
            return render_template('patient_dashboard.html', form=form, user=current_user, appointments=[])

        health_problem = form.health_problem.data
        specialty = HEALTH_PROBLEM_TO_SPECIALTY.get(health_problem, 'General')
        doctor = User.query.filter_by(is_doctor=True, specialty=specialty, availability_status='Available').first()
        if not doctor:
            flash(f'No available doctors for {health_problem}. Please try another health problem or date.', 'error')
            return render_template('patient_dashboard.html', form=form, user=current_user, appointments=[])

        doctor_daily_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.date >= day_start,
            Appointment.date <= day_end
        ).count()
        token_number = doctor_daily_appointments + 1
        avg_consultation_time = 15
        start_time = datetime.combine(selected_date, time(9, 0), tzinfo=timezone.utc)
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
            flash(f'Appointment booked successfully! Token Number: {token_number}. Doctor: {doctor.full_name}. Please arrive at {appointment_time.strftime("%I:%M %p")}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'error')
            print(f"Database error: {e}")
        return redirect(url_for('patient_dashboard'))

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
        current_date=current_date
    )

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, time(0, 0), tzinfo=timezone.utc)
    day_end = datetime.combine(today, time(23, 59, 59), tzinfo=timezone.utc)
    
    total_patients = User.query.filter_by(is_patient=True).count()
    todays_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).count()
    monthly_revenue = todays_appointments * 50
    average_rating = 4.5
    
    todays_appointments_query = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).order_by(Appointment.token_number.asc()).all()
    
    todays_appointments_data = []
    for appointment in todays_appointments_query:
        patient = db.session.get(User, appointment.user_id)
        todays_appointments_data.append({
            'appointment': appointment,
            'patient_initials': ''.join(word[0] for word in patient.full_name.split() if word)[:2] if patient else 'UN',
            'patient_name': patient.full_name if patient else 'Unknown'
        })
    
    recent_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.status == 'Completed'
    ).order_by(Appointment.date.desc()).limit(5).all()
    
    recent_patients = []
    for appointment in recent_appointments:
        patient = db.session.get(User, appointment.user_id)
        if patient:
            recent_patients.append({
                'initials': ''.join(word[0] for word in patient.full_name.split() if word)[:2],
                'name': patient.full_name,
                'age': relativedelta(datetime.now(timezone.utc), patient.dob).years if patient.dob else 'Unknown',
                'gender': patient.gender or 'Unknown',
                'last_visit': appointment.date.strftime('%Y-%m-%d')
            })
    
    return render_template(
        'doctor/doctor_dashboard.html',
        doctor_name=current_user.full_name,
        total_patients=total_patients,
        todays_appointments=todays_appointments,
        monthly_revenue=monthly_revenue,
        average_rating=average_rating,
        todays_appointments_data=todays_appointments_data,
        recent_patients=recent_patients
    )

@app.route('/appointments')
@login_required
def appointments():
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.date.asc()).all()
    appointments_data = []
    for appointment in appointments:
        patient = db.session.get(User, appointment.user_id)
        appointments_data.append({
            'appointment': appointment,
            'patient_name': patient.full_name if patient else 'Unknown'
        })
    return render_template('doctor/appointments.html', appointments_data=appointments_data)

@app.route('/patients')
@login_required
def patients():
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    # Get all patients this doctor has seen
    patient_ids = db.session.query(Appointment.user_id).filter_by(doctor_id=current_user.id).distinct().all()
    patients_data = []
    for (patient_id,) in patient_ids:
        patient = db.session.get(User, patient_id)
        if patient:
            last_appointment = Appointment.query.filter_by(user_id=patient.id, doctor_id=current_user.id).order_by(Appointment.date.desc()).first()
            patients_data.append({
                'id': patient.id,
                'name': patient.full_name,
                'age': relativedelta(datetime.now(timezone.utc), patient.dob).years if patient.dob else 'Unknown',
                'gender': patient.gender or 'Unknown',
                'last_visit': last_appointment.date.strftime('%Y-%m-%d') if last_appointment else 'N/A'
            })
    return render_template('doctor/patients.html', patients=patients_data)

@app.route('/prescriptions')
@login_required
def prescriptions():
    if not current_user.is_doctor:
        flash('Access denied. Doctors only.', 'error')
        return redirect(url_for('home'))
    
    # Placeholder for prescriptions page
    appointments = Appointment.query.filter_by(doctor_id=current_user.id, status='Completed').order_by(Appointment.date.desc()).all()
    prescriptions_data = [{'appointment_id': a.id, 'patient_name': db.session.get(User, a.user_id).full_name, 'date': a.date.strftime('%Y-%m-%d')} for a in appointments]
    return render_template('doctor/prescriptions.html', prescriptions=prescriptions_data)

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

@app.route('/appointment/<int:appointment_id>/reject', methods=['POST'])
@login_required
def reject_appointment(appointment_id):
    if not current_user.is_doctor:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    appointment.status = 'Rejected'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Appointment rejected'})

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
    
    form.notes.data = appointment.notes
    patient = db.session.get(User, appointment.user_id)
    return render_template('doctor/appointment_notes.html', form=form, appointment=appointment, patient=patient)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('home'))
    
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, time(0, 0), tzinfo=timezone.utc)
    day_end = datetime.combine(today, time(23, 59, 59), tzinfo=timezone.utc)
    
    today_appointments = Appointment.query.filter(
        Appointment.date >= day_start,
        Appointment.date <= day_end
    ).order_by(Appointment.date.asc()).all()
    
    total_patients = User.query.filter_by(is_patient=True).count()
    total_doctors = User.query.filter_by(is_doctor=True).count()
    total_appointments = Appointment.query.count()
    scheduled_appointments = Appointment.query.filter_by(status='Scheduled').count()
    consulting_appointments = Appointment.query.filter_by(status='Consulting').count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()
    
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

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username='admin', email='admin@example.com', full_name='Admin User', is_admin=True, is_doctor=False, is_patient=False)
        admin.set_password('admin123')
        doctor1 = User(username='doctor1', email='doctor1@example.com', full_name='Dr. John Doe', is_doctor=True, is_patient=False, specialty='General')
        doctor1.set_password('doctor123')
        doctor2 = User(username='doctor2', email='doctor2@example.com', full_name='Dr. Jane Smith', is_doctor=True, is_patient=False, specialty='Dermatologist')
        doctor2.set_password('doctor123')
        doctor3 = User(username='doctor3', email='doctor3@example.com', full_name='Dr. Mary Johnson', is_doctor=True, is_patient=False, specialty='Cardiologist')
        doctor3.set_password('doctor123')
        patient = User(username='patient1', email='patient1@example.com', full_name='Jane Doe', dob=datetime(1990, 1, 1, tzinfo=timezone.utc), gender='Female', health_conditions='Hypertension', is_patient=True)
        patient.set_password('patient123')
        db.session.add_all([admin, doctor1, doctor2, doctor3, patient])
        db.session.commit()
        print("Database initialized with test users: admin, doctor1-3, patient1")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
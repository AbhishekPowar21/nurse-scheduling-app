import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import get_db_connection  # Utility for database connection

# Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Helper function to send email
def send_otp_email(email, otp):
    sender_email = "abpo44580@gmail.com"  # Replace with your email
    sender_password = "almudpaqmcnjheti"  # Replace with your email password or app-specific password

    # Create message
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send the email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

    return True

# Function to generate OTP
def generate_otp():
    return random.randint(100000, 999999)


# Route for registration
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hospital_name = request.form.get('hospital_name')
        hospital_address = request.form.get('hospital_address')

        # Establish database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            # Check if the email is already registered
            cursor.execute('SELECT * FROM hospital_admin WHERE email = %s', (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email is already registered!', 'error')
                return redirect(url_for('auth.register'))

            # Generate OTP and send email
            otp = generate_otp()
            otp_sent = send_otp_email(email, otp)

            if otp_sent:
                # flash(f"OTP sent to {email}. Please check your inbox.", 'info')
                session['otp'] = otp  # Store OTP in session for later validation
                session['email'] = email  # Store email in session
                return redirect(url_for('auth.register'))  # Redirect to OTP verification page

            flash('Failed to send OTP. Please try again.', 'error')
            return redirect(url_for('auth.register'))

        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))

        finally:
            # Close database resources
            cursor.close()
            connection.close()

    return render_template('auth/register.html')


# Route to check if the email is already registered for sent OTP button
@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    email = request.form.get('email')

    # Establish database connection
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if the email is already registered
        cursor.execute('SELECT * FROM hospital_admin WHERE email = %s', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Return JSON response indicating the email is already registered
            return jsonify({'exists': True})
        else:
            # Return JSON response indicating the email is not registered
            return jsonify({'exists': False})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'exists': False})

    finally:
        # Close database resources
        cursor.close()
        connection.close()


# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"Before login check, session: {session}")  # Debugging session before login
    if 'user_id' in session:
        flash('You are already logged in!', 'info')
        return redirect(url_for('admin.admin_homepage'))  # Redirect if already logged in

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Retrieve user from the database
        cursor.execute('SELECT * FROM hospital_admin WHERE email = %s', (email,))
        user = cursor.fetchone()

        # Validate user credentials
        if user and user[3] == password:  # Compare passwords directly (no hashing)
            # Clear any existing session data (for example, in case the user is logging in again)
            session.clear()  # Clears all session data
            session['user_id'] = user[0]  # Set session data
            session['user_name'] = user[1]
            session['hospital_name'] = user[4]
            session.permanent = True  # Make the session permanent (to apply the 20-minute expiry)
            return redirect(url_for('admin.admin_homepage'))  # Redirect to admin homepage

        flash('Invalid email or password!', 'error')
        cursor.close()
        connection.close()
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


# Logout route
@auth_bp.route('/logout')
def logout():
    session.clear()  # Clear session data
    session.modified = True  # Ensure the session is modified to reflect the changes
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))  # Redirect to the home page after logout

import random, json
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

# Helper function to send email
def send_email(email, subject, body):
    sender_email = "abpo44580@gmail.com"  # Replace with your email
    sender_password = "almudpaqmcnjheti"  # Replace with your email password or app-specific password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

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
                

            # flash('Failed to send OTP. Please try again.', 'error')
            # return redirect(url_for('auth.register'))
        try:
            cursor.execute('INSERT INTO hospital_admin (name, email, password, hospital_name, hospital_address) VALUES (%s, %s, %s, %s, %s)',
                           (name, email, password, hospital_name, hospital_address))
            connection.commit()
            flash('Registration successful! Please log in.', 'success')
            # Send a welcome email after successful registration
            welcome_subject = "Welcome to NurseNetX"
            welcome_body = f"Dear {name},\n\nWelcome to NurseNetX, the Nurse Scheduling Software designed to make scheduling simple and healthcare better.\n\nWe are thrilled to have you on board!\n\nBest Regards,\nNurseNetX Team"
            send_email(email, welcome_subject, welcome_body)

            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"Error: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))

        finally:
            # Close database resources
            cursor.close()
            connection.close()

    return render_template('auth/register.html')


# Route to verify OTP
@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otp')
    session_otp = session.get('otp')

    if not session_otp:
        return jsonify({'success': False, 'message': 'OTP expired. Please request a new one.'})

    if entered_otp == str(session_otp):
        # OTP is correct, update the session or any other necessary state
        return jsonify({'success': True, 'message': 'OTP verified successfully.'})
    else:
        # OTP is incorrect
        return jsonify({'success': False, 'message': 'Invalid OTP. Please try again.'})


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
# In auth.py

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check hospital_admin table for matching email
        cursor.execute('SELECT * FROM hospital_admin WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and user[3] == password:  # Assuming the password is at index 3
            session.clear()  # Clear existing session data
            session['user_id'] = user[0]  # Hospital admin ID
            session['user_name'] = user[1]
            session['hospital_name'] = user[4]

            # Query notifications count from shift_swap_requests table for NurseAccepted status
            cursor.execute("SELECT COUNT(*) FROM shift_swap_requests WHERE status = 'NurseAccepted'")
            notification_count = cursor.fetchone()[0]
            session['notification_count'] = notification_count

            session.permanent = True  # Makes the session permanent (e.g., 20-minute expiry)
            cursor.close()
            connection.close()
            return redirect(url_for('admin.admin_homepage'))

        # If not found in hospital_admin, check the nurses table
        cursor.execute('SELECT * FROM nurses WHERE email = %s', (email,))
        nurse = cursor.fetchone()

        if nurse and nurse[4] == password:  # Adjust the index if the nurses table structure differs
            session.clear()  # Clear existing session data
            session['user_id'] = nurse[0]       # Nurse ID
            session['nurse_name'] = nurse[2]
            nurse_id = session['user_id']
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT admin_id FROM nurses WHERE nurse_id = %s", (nurse_id,))
            admin_row = cur.fetchone()
            if not admin_row:
                flash("Nurse record not found.", "error")
                return redirect(url_for('auth.login'))

            # Set admin_id in the session
            admin_id = admin_row[0]
            session['admin_id'] = admin_id
            print(admin_id)

            # Query the hospital_admin table to get the hospital_name for this admin_id
            cur.execute("SELECT hospital_name FROM hospital_admin WHERE admin_id = %s", (admin_id,))
            hospital_row = cur.fetchone()
            session['hospital_name'] = hospital_row[0]

            # Retrieve all schedule IDs for this nurse from the schedules table
            cursor.execute("SELECT schedule_id FROM schedules WHERE nurse_id = %s", (nurse[0],))
            nurse_schedule_rows = cursor.fetchall()
            current_schedule_ids = [row[0] for row in nurse_schedule_rows]

            # Query all pending shift swap requests
            cursor.execute("""
                SELECT request_id, requester_nurse_id, current_schedule_id, desired_schedule_id, status, notifications, created_at 
                FROM shift_swap_requests 
                WHERE status = 'Pending' 
                ORDER BY created_at DESC
            """)
            all_requests = cursor.fetchall()

            # Loop through requests and decode the JSON list for desired schedule IDs
            notifications = []
            for row in all_requests:
                req = {
                    'request_id': row[0],
                    'requester_nurse_id': row[1],
                    'current_schedule_id': row[2],
                    'desired_schedule_id': row[3],  # This is a JSON string containing eligible schedule ids
                    'status': row[4],
                    'notifications': row[5],
                    'created_at': row[6]
                }
                # Decode the JSON list
                desired_schedule_ids = json.loads(req['desired_schedule_id'])
                # If any of the nurse's schedule ids appear in the eligible list, add the request to notifications.
                if any(sched_id in desired_schedule_ids for sched_id in current_schedule_ids):
                    notifications.append(req)

            # Set the notification count in session based on the filtered notifications
            notification_count = len(notifications)
            session['notification_count'] = notification_count
            print("Notification Count:", notification_count)

            session.permanent = True
            cursor.close()
            connection.close()
            return redirect(url_for('nurse.nurse_homepage'))
        
        # If no matching user or nurse is found, flash an error
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

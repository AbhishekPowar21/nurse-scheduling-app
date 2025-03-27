from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from database import get_db_connection
import json
import random, copy  # For genetic algorithm and simulation
import math  # For any mathematical operations
from datetime import datetime

nurse_bp = Blueprint('nurse', __name__)

@nurse_bp.route('/nurse_homepage')
def nurse_homepage():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve all schedule IDs for this nurse from the schedules table
    nurse_id = session.get('user_id')
    cursor.execute("SELECT schedule_id FROM schedules WHERE nurse_id = %s", (nurse_id,))
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
        # If any of the nurse's schedule IDs appear in the eligible list, add the request to notifications.
        if any(sched_id in desired_schedule_ids for sched_id in current_schedule_ids):
            notifications.append(req)

    # Set the notification count in session based on the filtered notifications
    notification_count = len(notifications)
    session['notification_count'] = notification_count

    cursor.close()
    conn.close()
    return render_template(
        'nurse/nurse_homepage.html',
        nurse_name=session.get('nurse_name'),
        notification_count=notification_count
    )

@nurse_bp.route('/nurse_dashboard', methods=['GET'])
def nurse_dashboard():
    if 'user_id' not in session:
        flash("Please log in as a nurse to access your dashboard.", "error")
        return redirect(url_for('auth.login'))
    
    nurse_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Get the nurse's admin_id from the nurses table
    cur.execute("SELECT admin_id FROM nurses WHERE nurse_id = %s", (nurse_id,))
    admin_row = cur.fetchone()
    if not admin_row:
        flash("Nurse record not found.", "error")
        return redirect(url_for('auth.login'))
    admin_id = admin_row[0]

    # Retrieve the schedule for the logged-in nurse (including schedule_id)
    cur.execute("""
        SELECT schedule_id, shift_day, shift_start, shift_end
        FROM schedules
        WHERE nurse_id = %s AND admin_id = %s
    """, (nurse_id, admin_id))
    schedule_data = cur.fetchall()

    # Create a dictionary for days of the week and include schedule_id in each entry
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: [] for day in days}
    for row in schedule_data:
        schedule_id, shift_day, shift_start, shift_end = row
        if shift_day in schedule:
            schedule[shift_day].append({
                "schedule_id": schedule_id,
                "shift_start": shift_start,
                "shift_end": shift_end
            })

    # Query the latest shift swap request that involves this nurse (either as requester or target)
    cur.execute("""
        SELECT current_schedule_id, desired_schedule_id
        FROM shift_swap_requests
        WHERE admin_id = %s AND (requester_nurse_id = %s OR target_nurse_id = %s)
        ORDER BY created_at DESC
        LIMIT 1
    """, (admin_id, nurse_id, nurse_id))
    latest_swap = cur.fetchone()
    swapped_schedule_ids = []
    print("DEBUG: latest_swap raw output:", latest_swap)

    if latest_swap:
        import json
        try:
            print("DEBUG: Latest swap raw data:", latest_swap)
            # Extract current_schedule_id and desired_schedule_id data from the swap request
            current_schedule_id = latest_swap[0]
            desired_schedule_data = latest_swap[1]
            print("DEBUG: current_schedule_id:", current_schedule_id)
            print("DEBUG: desired_schedule_data (raw):", desired_schedule_data)
            
            # Parse the JSON list of desired schedule IDs
            desired_schedule_ids = []
            if desired_schedule_data:
                desired_schedule_ids = json.loads(desired_schedule_data)
            print("DEBUG: Parsed desired_schedule_ids:", desired_schedule_ids)
            
            # Combine the current schedule id and the desired schedule ids into one list
            all_swap_ids = []
            if current_schedule_id:
                all_swap_ids.append(current_schedule_id)
            if desired_schedule_ids:
                all_swap_ids.extend(desired_schedule_ids)
            print("DEBUG: Combined swap schedule IDs:", all_swap_ids)
            
            # If we have any schedule IDs to highlight, filter them by ensuring they belong to this nurse
            if all_swap_ids:
                placeholders = ','.join(['%s'] * len(all_swap_ids))
                print("DEBUG: Placeholders for query:", placeholders)
                
                query = f"""
                    SELECT schedule_id
                    FROM schedules
                    WHERE schedule_id IN ({placeholders}) AND nurse_id = %s
                """
                params = tuple(all_swap_ids) + (nurse_id,)
                print("DEBUG: Query parameters:", params)
                
                cur.execute(query, params)
                result = cur.fetchall()
                print("DEBUG: Result from schedules query:", result)
                
                swapped_schedule_ids = [str(row[0]) for row in result]
                print("DEBUG: Filtered swapped_schedule_ids:", swapped_schedule_ids)
            else:
                print("DEBUG: No swap schedule IDs found after combining.")
        except Exception as e:
            print("DEBUG: Error while processing swap request:", e)
            swapped_schedule_ids = []

    cur.close()
    conn.close()
    return render_template(
        'nurse/nurse_dashboard.html',
        nurse_name=session.get('nurse_name'),
        schedule=schedule,
        swapped_schedule_ids=swapped_schedule_ids
    )




from datetime import datetime
import json
from flask import request, session, flash, redirect, url_for, render_template
# Assume get_db_connection() and nurse_bp have been defined/imported elsewhere

@nurse_bp.route('/shift_swap', methods=['GET', 'POST'])
def shift_swap():
    # Ensure nurse is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))
    
    current_nurse_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()

    # Retrieve the nurse's admin_id for filtering records
    cur.execute("SELECT admin_id FROM nurses WHERE nurse_id = %s", (current_nurse_id,))
    admin_row = cur.fetchone()
    if not admin_row:
        flash("Nurse record not found.", "error")
        return redirect(url_for('nurse.nurse_homepage'))
    admin_id = admin_row[0]

    # Retrieve all scheduled shifts for the current admin along with nurse names
    cur.execute("""
        SELECT s.schedule_id, s.nurse_id, n.name AS nurse_name, s.shift_day, s.shift_start, s.shift_end, s.status
        FROM schedules s
        JOIN nurses n ON s.nurse_id = n.nurse_id
        WHERE s.status = 'Scheduled' AND s.admin_id = %s
    """, (admin_id,))
    schedule_data = cur.fetchall()

    # Define days and prepare data structures
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: [] for day in days}
    my_schedules = []

    for entry in schedule_data:
        # entry: (schedule_id, nurse_id, nurse_name, shift_day, shift_start, shift_end, status)
        schedule_id, nurse_id, nurse_name, shift_day, shift_start, shift_end, status = entry
        schedule_entry = {
            "schedule_id": schedule_id,
            "nurse_id": nurse_id,
            "nurse_name": nurse_name,
            "shift_day": shift_day,
            "shift_start": shift_start,
            "shift_end": shift_end
        }
        if shift_day in schedule:
            schedule[shift_day].append(schedule_entry)
        if nurse_id == current_nurse_id:
            my_schedules.append(schedule_entry)

    # Determine whether to display the schedule table
    display_style = "block" if any(schedule.values()) else "none"

    # Compute allowed desired days (only days after the current day)
    current_day = datetime.now().strftime("%A")
    try:
        current_index = days.index(current_day)
    except ValueError:
        current_index = -1
    allowed_desired_days = days[current_index+1:] if current_index < len(days)-1 else []

    if request.method == 'POST':
        current_schedule_id = request.form.get('current_schedule_id')
        desired_day = request.form.get('desired_day')
        desired_shift = request.form.get('desired_shift')

        # Validate that the desired day is allowed
        if desired_day not in allowed_desired_days:
            flash("Selected desired day is not allowed.", "error")
            return redirect(url_for('nurse.shift_swap'))

        # Query eligible schedules for the desired day and shift (with nurse names), filtered by admin_id
        cur.execute("""
            SELECT s.schedule_id, s.nurse_id, n.name AS nurse_name, s.shift_day, s.shift_start, s.shift_end
            FROM schedules s
            JOIN nurses n ON s.nurse_id = n.nurse_id
            WHERE s.shift_day = %s AND s.shift_end = %s AND s.status = 'Scheduled' AND s.admin_id = %s
        """, (desired_day, desired_shift, admin_id))
        eligible_schedules = cur.fetchall()

        # Gather schedule IDs from eligible nurses (exclude the requester)
        eligible_schedule_ids = []
        for sched in eligible_schedules:
            sched_id, nurse_id, nurse_name, shift_day, shift_start, shift_end = sched
            if nurse_id == current_nurse_id:
                continue
            eligible_schedule_ids.append(sched_id)

        if not eligible_schedule_ids:
            flash("No eligible nurses found for the selected day and shift.", "error")
            cur.close()
            conn.close()
            return redirect(url_for('nurse.shift_swap'))

        # Convert the list to a JSON string for storage
        desired_schedule_json = json.dumps(eligible_schedule_ids)
        notification_msg = f"Request for swap on {desired_day} - {desired_shift}"

        # Insert the swap request and include the admin_id for filtering
        cur.execute("""
            INSERT INTO shift_swap_requests 
              (requester_nurse_id, current_schedule_id, desired_schedule_id, target_nurse_id, status, notifications, admin_id)
            VALUES (%s, %s, %s, NULL, 'Pending', %s, %s)
        """, (current_nurse_id, current_schedule_id, desired_schedule_json, notification_msg, admin_id))
        conn.commit()
        cur.close()
        conn.close()

        flash("Shift swap request submitted successfully.", "success")
        return redirect(url_for('nurse.shift_swap'))

    cur.close()
    conn.close()

    # Query pending swap requests for the current nurse (as requester)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT request_id, current_schedule_id, desired_schedule_id, status, notifications, created_at 
        FROM shift_swap_requests 
        WHERE requester_nurse_id = %s AND (status = 'Pending' OR status = 'NurseAccepted' OR status = 'AdminApproved') AND admin_id = %s
        ORDER BY created_at DESC
    """, (current_nurse_id, admin_id))
    pending_requests_data = cur.fetchall()
    pending_requests = []
    for row in pending_requests_data:
        pending_requests.append({
            'request_id': row[0],
            'current_schedule_id': row[1],
            'desired_schedule_id': row[2],
            'status': row[3],
            'notifications': row[4],
            'created_at': row[5]
        })
    cur.close()
    conn.close()

    conn = get_db_connection()
    cur = conn.cursor()

    # Retrieve the latest swap request that involves this nurse (either as requester or target)
    # Now select requester_nurse_id and target_nurse_id for filtering the schedules later.
    cur.execute("""
        SELECT current_schedule_id, desired_schedule_id, requester_nurse_id, target_nurse_id
        FROM shift_swap_requests
        WHERE admin_id = %s AND (requester_nurse_id = %s OR target_nurse_id = %s)
        ORDER BY created_at DESC
        LIMIT 1
    """, (admin_id, current_nurse_id, current_nurse_id))
    latest_swap = cur.fetchone()
    swapped_schedule_ids = []
    print("DEBUG: latest_swap raw output:", latest_swap)

    if latest_swap:
        try:
            current_schedule_id = latest_swap[0]
            desired_schedule_data = latest_swap[1]
            requester_nurse_id = latest_swap[2]
            target_nurse_id = latest_swap[3]
            print("DEBUG: current_schedule_id:", current_schedule_id)
            print("DEBUG: desired_schedule_data (raw):", desired_schedule_data)
            print("DEBUG: requester_nurse_id:", requester_nurse_id)
            print("DEBUG: target_nurse_id:", target_nurse_id)
            
            # Parse the JSON list of desired schedule IDs
            desired_schedule_ids = json.loads(desired_schedule_data) if desired_schedule_data else []
            print("DEBUG: Parsed desired_schedule_ids:", desired_schedule_ids)
            
            # Combine the current schedule id and the desired schedule ids into one list
            all_swap_ids = []
            if current_schedule_id:
                all_swap_ids.append(current_schedule_id)
            if desired_schedule_ids:
                all_swap_ids.extend(desired_schedule_ids)
            print("DEBUG: Combined swap schedule IDs:", all_swap_ids)
            
            # Now filter these schedule IDs to include only those belonging to the requester and target nurse
            if all_swap_ids:
                placeholders = ','.join(['%s'] * len(all_swap_ids))
                query = f"""
                    SELECT schedule_id
                    FROM schedules
                    WHERE schedule_id IN ({placeholders}) AND nurse_id IN (%s, %s)
                """
                params = tuple(all_swap_ids) + (requester_nurse_id, target_nurse_id)
                print("DEBUG: Query parameters:", params)
                
                cur.execute(query, params)
                result = cur.fetchall()
                print("DEBUG: Result from schedules query:", result)
                
                swapped_schedule_ids = [str(row[0]) for row in result]
                print("DEBUG: Highlighted swapped_schedule_ids:", swapped_schedule_ids)
            else:
                print("DEBUG: No swap schedule IDs found after combining.")
        except Exception as e:
            print("DEBUG: Error while processing swap request:", e)
            swapped_schedule_ids = []

    cur.close()
    conn.close()

    return render_template('nurse/shift_swap.html', 
                           schedule=schedule, 
                           display_style=display_style,
                           my_schedules=my_schedules,
                           allowed_desired_days=allowed_desired_days,
                           pending_requests=pending_requests,
                           swapped_schedule_ids=swapped_schedule_ids)



@nurse_bp.route('/notifications', methods=['GET', 'POST'])
def notifications():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    current_nurse_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()

    # Get the nurse's admin_id
    cur.execute("SELECT admin_id FROM nurses WHERE nurse_id = %s", (current_nurse_id,))
    admin_row = cur.fetchone()
    if not admin_row:
        flash("Nurse record not found.", "error")
        return redirect(url_for('nurse.nurse_homepage'))
    admin_id = admin_row[0]

    # Retrieve swap requests:
    # - For statuses 'Pending' or 'NurseAccepted', show requests for this admin.
    # - For status 'AdminApproved', only show if the current nurse is the target nurse.
    cur.execute("""
        SELECT request_id, requester_nurse_id, current_schedule_id, desired_schedule_id, 
               target_nurse_id, status, notifications, created_at 
        FROM shift_swap_requests 
        WHERE ((status IN ('Pending', 'NurseAccepted', 'AdminRejected') AND admin_id = %s)
               OR (status = 'AdminApproved' AND target_nurse_id = %s))
        ORDER BY created_at DESC
    """, (admin_id, current_nurse_id))

    all_requests = cur.fetchall()

    # Retrieve this nurse's schedule IDs (for filtering non-adminapproved requests)
    current_schedule_ids = get_nurse_schedule_ids(current_nurse_id)

    notifications_list = []
    for row in all_requests:
        req = {
            'request_id': row[0],
            'requester_nurse_id': row[1],
            'current_schedule_id': row[2],
            'desired_schedule_id': row[3],  # JSON string for eligible schedule IDs
            'target_nurse_id': row[4],
            'status': row[5],
            'notifications': row[6],
            'created_at': row[7]
        }
        # For AdminApproved requests, the SQL already filters to current nurse, so add directly.
        if req['status'] == 'AdminApproved':
            notifications_list.append(req)
        else:
            # For Pending and NurseAccepted requests, decode the JSON list of eligible schedule IDs.
            desired_schedule_ids = json.loads(req['desired_schedule_id'])
            # If any of the nurse's schedule IDs appear in the eligible list, add the request.
            if any(sched_id in desired_schedule_ids for sched_id in current_schedule_ids):
                notifications_list.append(req)

    cur.close()
    conn.close()
    
    return render_template('nurse/notifications.html', notifications=notifications_list)

def get_nurse_schedule_ids(nurse_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT schedule_id FROM schedules WHERE nurse_id = %s", (nurse_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row[0] for row in rows]

@nurse_bp.route('/respond_swap', methods=['POST'])
def respond_swap():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    request_id = request.form.get('request_id')
    action = request.form.get('swap_action')
    current_nurse_id = session.get('user_id')

    if not request_id or action != 'accept':
        flash("Invalid action.", "error")
        return redirect(url_for('nurse.notifications'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get the nurse's admin_id
    cur.execute("SELECT admin_id FROM nurses WHERE nurse_id = %s", (current_nurse_id,))
    admin_row = cur.fetchone()
    if not admin_row:
        flash("Nurse record not found.", "error")
        cur.close()
        conn.close()
        return redirect(url_for('nurse.nurse_homepage'))
    admin_id = admin_row[0]

    # Retrieve the swap request (filtering by admin_id)
    cur.execute("""
        SELECT request_id, requester_nurse_id, current_schedule_id, desired_schedule_id, target_nurse_id, status
        FROM shift_swap_requests
        WHERE request_id = %s AND admin_id = %s
    """, (request_id, admin_id))
    row = cur.fetchone()
    if not row:
        flash("Swap request not found.", "error")
        cur.close()
        conn.close()
        return redirect(url_for('nurse.notifications'))

    # Update the swap request: assign this nurse as the target and mark as NurseAccepted
    cur.execute("""
        UPDATE shift_swap_requests
        SET target_nurse_id = %s, status = 'NurseAccepted'
        WHERE request_id = %s
    """, (current_nurse_id, request_id))
    conn.commit()
    flash("Swap request accepted. Awaiting admin approval.", "success")
    cur.close()
    conn.close()
    return redirect(url_for('nurse.notifications'))

@nurse_bp.route('/edit_nurse_info', methods=['GET', 'POST'])
def edit_nurse_info():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))
    
    nurse_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'GET':
        # Fetch the current nurse's information
        cur.execute("""
            SELECT name, email, phone, shift_preference, sleep_hours, category, department, status
            FROM nurses
            WHERE nurse_id = %s
        """, (nurse_id,))
        nurse_info = cur.fetchone()

        if nurse_info:
            return render_template('nurse/edit_nurse_info.html', nurse_info=nurse_info)
        else:
            flash('Nurse information not found.', 'error')
            return redirect(url_for('nurse.nurse_homepage'))
    
    elif request.method == 'POST':
        # Get the edited data from the form
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        shift_preference = request.form.get('shift_preference')
        sleep_hours = request.form.get('sleep_hours')
        category = request.form.get('category')
        department = request.form.get('department')
        status = request.form.get('status')
        
        try:
            # Update the nurse's information
            cur.execute("""
                UPDATE nurses
                SET name = %s, email = %s, phone = %s, shift_preference = %s, sleep_hours = %s, category = %s, department = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE nurse_id = %s
            """, (name, email, phone, shift_preference, sleep_hours, category, department, status, nurse_id))
            conn.commit()
            flash('Your information has been updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error updating information: {e}', 'error')
        finally:
            cur.close()
            conn.close()
        
        return redirect(url_for('nurse.edit_nurse_info'))

@nurse_bp.route('/notification_count')
def notification_count():
    if 'user_id' not in session:
        return jsonify({'notification_count': 0})
    
    current_nurse_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get nurse's admin_id
    cur.execute("SELECT admin_id FROM nurses WHERE nurse_id = %s", (current_nurse_id,))
    admin_row = cur.fetchone()
    if not admin_row:
        cur.close()
        conn.close()
        return jsonify({'notification_count': 0})
    admin_id = admin_row[0]
    
    # Retrieve all schedule IDs for this nurse from the schedules table
    cur.execute("SELECT schedule_id FROM schedules WHERE nurse_id = %s AND admin_id = %s", (current_nurse_id, admin_id))
    nurse_schedule_rows = cur.fetchall()
    current_schedule_ids = [row[0] for row in nurse_schedule_rows]
    
    # Fetch all pending shift swap requests for this admin
    cur.execute("""
        SELECT request_id, requester_nurse_id, current_schedule_id, desired_schedule_id, status, notifications, created_at 
        FROM shift_swap_requests 
        WHERE status = 'Pending' AND admin_id = %s
        ORDER BY created_at DESC
    """, (admin_id,))
    all_requests = cur.fetchall()
    
    # Filter notifications: Only include those where any of the nurse's schedule IDs appears in the desired_schedule_id JSON list.
    notifications = []
    for row in all_requests:
        desired_schedule_ids = json.loads(row[3])
        if any(sched_id in desired_schedule_ids for sched_id in current_schedule_ids):
            notifications.append(row)
    
    count = len(notifications)
    cur.close()
    conn.close()
    return jsonify({'notification_count': count})

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from database import get_db_connection
import random  # For genetic algorithm and simulation
import math  # For any mathematical operations
from datetime import datetime
from collections import defaultdict
import random, copy
admin_bp = Blueprint('admin', __name__)

# Dashboard route
@admin_bp.route('/admin_homepage')
def admin_homepage():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    return render_template(
        'admin/admin_homepage.html',
        hospital_name=session.get('hospital_name'),
        admin_name=session.get('user_name')
    )




@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()
    admin_id = session['user_id']

    # Fetch total number of nurses
    cur.execute("SELECT COUNT(*) FROM nurses WHERE admin_id = %s", (admin_id,))
    total_nurses = cur.fetchone()[0]

    # Fetch active and inactive nurses
    cur.execute("SELECT COUNT(*) FROM nurses WHERE admin_id = %s AND status = 'Active'", (admin_id,))
    active_nurses = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM nurses WHERE admin_id = %s AND status = 'Inactive'", (admin_id,))
    inactive_nurses = cur.fetchone()[0]

    # Fetch category breakdown
    cur.execute("SELECT department, COUNT(*) FROM nurses WHERE admin_id = %s GROUP BY department", (admin_id,))
    category_breakdown = cur.fetchall()  # This will be a list of tuples (e.g., [("Senior", 12), ("Junior", 10)])

    cur.execute("SELECT category, COUNT(*) FROM nurses WHERE admin_id = %s GROUP BY category", (admin_id,))
    category = cur.fetchall()  # This will be a list of tuples (e.g., [("Senior", 12), ("Junior", 10)])

    cur.close()
    conn.close()

    # Pass the data to the template
    return render_template(
        'admin/admin_dashboard.html',
        total_nurses=total_nurses,
        active_nurses=active_nurses,
         category_breakdown=category_breakdown,
         category=category,
        inactive_nurses=inactive_nurses,
       
    )

# Manage Nurses Route
@admin_bp.route('/manage_nurses', methods=['GET', 'POST'])
def manage_nurses():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()
    admin_id = session['user_id']

    # Fetch nurses for the current admin
    query = "SELECT * FROM nurses WHERE admin_id = %s"
    cur.execute(query, (admin_id,))
    nurses = cur.fetchall()

    # Handle search/filter
    if request.method == 'POST':
        search_query = request.form.get('search')
        filter_category = request.form.get('filter_category')

        if search_query or filter_category:
            sql = "SELECT * FROM nurses WHERE admin_id = %s"
            params = [admin_id]

            if search_query:
                sql += " AND (LOWER(name) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s))"
                params.extend([f"%{search_query}%", f"%{search_query}%"])

            if filter_category:
                sql += " AND category = %s"
                params.append(filter_category)

            cur.execute(sql, tuple(params))
            nurses = cur.fetchall()

    # Render content-only template for AJAX
    return render_template('admin/manage_nurse.html', nurses=nurses)

# Add Nurse Route
@admin_bp.route('/add_nurse', methods=['POST'])
def add_nurse():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    data = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    admin_id = session['user_id']

    try:
        cur.execute("""
            INSERT INTO nurses (admin_id, name, email, phone, shift_preference, sleep_hours, category, department, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            admin_id, data['name'], data['email'], data['phone'], 
            data['shift_preference'], data['sleep_hours'], data['category'],
            data['department'], 'Active'  # Assuming 'Active' by default
        ))
        conn.commit()
        flash('Nurse added successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error adding nurse: {e}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.manage_nurses'))

@admin_bp.route('/edit_nurse/<int:nurse_id>', methods=['GET', 'POST'])
def edit_nurse(nurse_id):
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch the current nurse's information
    cur.execute("SELECT * FROM nurses WHERE nurse_id = %s", (nurse_id,))
    nurse = cur.fetchone()

    if nurse is None:
        flash('Nurse not found!', 'error')
        return redirect(url_for('admin.manage_nurses'))

    # If it's a POST request, handle the form submission
    if request.method == 'POST':
        try:
            # Get updated data from the form
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            shift_preference = request.form['shift_preference']
            sleep_hours = request.form['sleep_hours']
            category = request.form['category']
            department = request.form['department']
            status = request.form['status']

            # Update the nurse's record in the database
            cur.execute("""
                UPDATE nurses
                SET name = %s, email = %s, phone = %s, shift_preference = %s, 
                    sleep_hours = %s, category = %s, department = %s, status = %s
                WHERE nurse_id = %s
            """, (
                name, email, phone, shift_preference, sleep_hours, category, department, status, nurse_id
            ))
            conn.commit()

            flash('Nurse updated successfully!', 'success')
            return redirect(url_for('admin.manage_nurses'))
        except Exception as e:
            flash(f"Error updating nurse: {e}", 'error')
            conn.rollback()

    # Render the edit form with the nurse's data
    return render_template('admin/edit_nurse.html', nurse=nurse)


# Delete Nurse Route
@admin_bp.route('/delete_nurse/<int:nurse_id>', methods=['POST'])
def delete_nurse(nurse_id):
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM nurses WHERE nurse_id = %s AND admin_id = %s", (nurse_id, session['user_id']))
        conn.commit()
        flash('Nurse deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting nurse: {e}', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('admin.manage_nurses'))

@admin_bp.route('/edit_admin_info', methods=['GET', 'POST'])
def edit_admin_info():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    admin_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'GET':
        # Fetch the current admin's information
        cur.execute("""
            SELECT name, email, hospital_name, hospital_address
            FROM hospital_admin
            WHERE admin_id = %s
        """, (admin_id,))
        admin_info = cur.fetchone()

        if admin_info:
            # Return the current info to the template
            return render_template('admin/edit_admin_info.html', admin_info=admin_info)
        else:
            flash('Admin information not found.', 'error')
            return redirect(url_for('admin.admin_homepage'))

    elif request.method == 'POST':
        # Get the edited data from the form
        name = request.form.get('name')
        email = request.form.get('email')
        hospital_name = request.form.get('hospital_name')
        hospital_address = request.form.get('hospital_address')

        try:
            # Update the admin's information
            cur.execute("""
                UPDATE hospital_admin
                SET name = %s, email = %s, hospital_name = %s, hospital_address = %s, updated_at = CURRENT_TIMESTAMP
                WHERE admin_id = %s
            """, (name, email, hospital_name, hospital_address, admin_id))
            conn.commit()

            flash('Your information has been updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error updating information: {e}', 'error')
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('admin.edit_admin_info'))


def get_shift_end_time(shift_start):
    """
    Function to map shift start time to a human-readable combined shift time.
    """
    shift_end_map = {
        '08:00:00': '8 AM to 4 PM',   # 8 AM to 4 PM shift
        '16:00:00': '4 PM to 12 AM',  # 4 PM to 12 AM shift
        '00:00:00': '12 AM to 8 AM'   # 12 AM to 8 AM shift
    }
    return shift_end_map.get(shift_start, 'Unknown')



@admin_bp.route('/generate_schedule', methods=['GET', 'POST'])
def generate_schedule():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Query all nurses
    cur.execute("SELECT nurse_id, name FROM nurses")
    nurses = cur.fetchall()
    if not nurses:
        flash("No nurses found.", "error")
        cur.close()
        conn.close()
        return render_template('admin/generate_schedule.html', schedule=None)

    nurse_ids = [n[0] for n in nurses]
    nurse_map = {n[0]: n[1] for n in nurses}

    # Define days and shift labels
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    shift_labels = ['8 AM to 4 PM', '4 PM to 12 AM', '12 AM to 8 AM']
    total_shifts = len(days) * len(shift_labels)  # 21 shifts per week

    # --- NEW: Read user-specified nurses per shift from the form ---
    nurses_per_shift_input = request.form.get('nurses_per_shift')
    try:
        user_nurses_per_shift = int(nurses_per_shift_input)
    except (TypeError, ValueError):
        user_nurses_per_shift = 0

    # Build shift_info list as a list of tuples (day, shift, target number of nurses)
    shift_info = []
    if user_nurses_per_shift > 0:
        # Use the user-provided fixed number for each shift.
        for day in days:
            for shift in shift_labels:
                shift_info.append((day, shift, user_nurses_per_shift))
        total_nurses_required = user_nurses_per_shift * total_shifts
        if total_nurses_required > len(nurse_ids):
            flash("Warning: Not enough nurses available for the specified nurses per shift. Some shifts may be underfilled.", "warning")
    else:
        # Default balanced assignment if no user input or invalid input provided.
        base = len(nurse_ids) // total_shifts
        remainder = len(nurse_ids) % total_shifts
        shift_index = 0
        for day in days:
            for shift in shift_labels:
                target = base + 1 if shift_index < remainder else base
                shift_info.append((day, shift, target))
                shift_index += 1

    # Genetic Algorithm (GA) Parameters
    POP_SIZE = 50
    GENERATIONS = 100
    MUTATION_RATE = 0.1

    # Define disallowed consecutive shifts (if a nurse works one shift, they should not immediately work its disallowed next shift)
    disallowed = {
        '8 AM to 4 PM': '4 PM to 12 AM',
        '4 PM to 12 AM': '12 AM to 8 AM',
        '12 AM to 8 AM': '8 AM to 4 PM'
    }

    def create_candidate():
        """Create a random candidate schedule."""
        candidate = []
        for (day, shift, target) in shift_info:
            if target <= len(nurse_ids):
                candidate.append(random.sample(nurse_ids, target))
            else:
                candidate.append([random.choice(nurse_ids) for _ in range(target)])
        return candidate

    def initial_population():
        """Generate the initial population."""
        return [create_candidate() for _ in range(POP_SIZE)]

    def fitness(candidate):
        """Compute a fitness penalty for a candidate schedule."""
        penalty = 0
        # Build assignments per nurse: nurse_id -> list of (shift index, day, shift_label)
        assignments = {nid: [] for nid in nurse_ids}
        for idx, gene in enumerate(candidate):
            day, shift, target = shift_info[idx]
            # Penalty for duplicate assignments within the same shift
            if len(gene) != len(set(gene)):
                penalty += 5 * (len(gene) - len(set(gene)))
            for nurse_id in gene:
                assignments[nurse_id].append((idx, day, shift))
        # Check for disallowed consecutive shifts
        for nid, asg in assignments.items():
            asg.sort(key=lambda x: x[0])
            for i in range(len(asg) - 1):
                _, _, shift_current = asg[i]
                _, _, shift_next = asg[i + 1]
                if disallowed.get(shift_current) == shift_next:
                    penalty += 10
        # Penalize uneven distribution of shifts among nurses.
        total_assignments = sum(len(gene) for gene in candidate)
        ideal = total_assignments / len(nurse_ids)
        for nid in nurse_ids:
            count = len(assignments[nid])
            penalty += abs(count - ideal)
        return penalty

    def selection(population):
        """Tournament selection: choose the best out of 3 randomly picked candidates."""
        selected = []
        for _ in range(len(population)):
            contenders = random.sample(population, 3)
            best = min(contenders, key=fitness)
            selected.append(best)
        return selected

    def crossover(parent1, parent2):
        """Uniform crossover: for each shift gene, randomly choose from one parent."""
        child = []
        for gene1, gene2 in zip(parent1, parent2):
            if random.random() < 0.5:
                child.append(copy.deepcopy(gene1))
            else:
                child.append(copy.deepcopy(gene2))
        return child

    def mutate(candidate):
        """Mutate a candidate by randomly replacing one nurse in a gene."""
        for i in range(len(candidate)):
            if random.random() < MUTATION_RATE:
                gene = candidate[i]
                pos = random.randrange(len(gene))
                possible = [nid for nid in nurse_ids if nid not in gene]
                if possible:
                    gene[pos] = random.choice(possible)
                else:
                    gene[pos] = random.choice(nurse_ids)
        return candidate

    def genetic_algorithm():
        """Run the GA to generate a candidate schedule."""
        population = initial_population()
        best_candidate = None
        best_fit = float('inf')
        for generation in range(GENERATIONS):
            population.sort(key=fitness)
            current_best = population[0]
            current_fit = fitness(current_best)
            if current_fit < best_fit:
                best_fit = current_fit
                best_candidate = current_best
            if best_fit == 0:
                break  # Ideal candidate found
            selected = selection(population)
            next_population = []
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    child1 = crossover(selected[i], selected[i + 1])
                    child2 = crossover(selected[i + 1], selected[i])
                    mutate(child1)
                    mutate(child2)
                    next_population.extend([child1, child2])
                else:
                    next_population.append(selected[i])
            population = next_population
        return best_candidate

    if request.method == 'POST':
        candidate = genetic_algorithm()

        # Delete previous schedules
        cur.execute("DELETE FROM schedules WHERE status = 'Scheduled'")
        conn.commit()

        # Insert the generated schedule into the database
        for idx, gene in enumerate(candidate):
            day, shift_label, target = shift_info[idx]
            # Assume shift_start is derived from the label's first part
            shift_start = shift_label.split(' to ')[0]
            for nurse_id in gene:
                cur.execute(
                    """
                    INSERT INTO schedules (nurse_id, shift_day, shift_start, shift_end, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (nurse_id, day, shift_start, shift_label, "Scheduled")
                )
        conn.commit()
        flash("Schedule generated successfully!", "success")

    # Load any preexisting schedule data to pass to the template
    cur.execute(
        """
        SELECT s.schedule_id, n.name AS nurse_name, s.nurse_id, s.shift_day, s.shift_start, s.shift_end, s.status 
        FROM schedules s
        JOIN nurses n ON s.nurse_id = n.nurse_id
        WHERE s.status = 'Scheduled'
        """
    )
    schedule_data = cur.fetchall()
    schedule = {day: [] for day in days}
    for entry in schedule_data:
        day = entry[3]
        schedule[day].append({
            "shift_start": entry[4],
            "shift_end": entry[5],
            "nurse_name": entry[1]
        })

    cur.close()
    conn.close()
    return render_template('admin/generate_schedule.html', schedule=schedule)

def get_next_shift(last_shift):
    # Helper function to get the next shift for the nurse
    shift_times = {'08:00:00': '16:00:00', '16:00:00': '00:00:00', '00:00:00': '08:00:00'}
    return shift_times.get(last_shift, None)

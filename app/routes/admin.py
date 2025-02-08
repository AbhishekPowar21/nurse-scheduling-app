from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from database import get_db_connection
import random  # For genetic algorithm and simulation
import math  # For any mathematical operations
from datetime import datetime

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


# Dashboard route
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



    cur.close()
    conn.close()

    

    return render_template(
        'admin/admin_dashboard.html',
        total_nurses=total_nurses
        
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

@admin_bp.route('/edit_nurse/<int:nurse_id>', methods=['POST'])
def edit_nurse(nurse_id):
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    if request.is_json:
        data = request.get_json()
        name = data.get('0')
        email = data.get('1')
        phone = data.get('2')
        shift_preference = data.get('3')
        sleep_hours = data.get('4')
        category = data.get('5')
        department = data.get('6')
        status = data.get('7')

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE nurses
                SET name = %s, email = %s, phone = %s, shift_preference = %s, 
                    sleep_hours = %s, category = %s, department = %s, status = %s
                WHERE nurse_id = %s AND admin_id = %s
            """, (
                name, email, phone, shift_preference, sleep_hours, category, department, status,
                nurse_id, session['user_id']
            ))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Nurse updated successfully!'})

        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': f'Error updating nurse: {e}'}), 500

        finally:
            cur.close()
            conn.close()
    
    flash('Invalid request method.', 'error')
    return redirect(url_for('admin.manage_nurses'))


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



# Define your Genetic Algorithm functions

# Function to map a shift time to a day of the week (this logic can be adjusted)
def get_day_of_week(shift_time):
    day_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    shift_hour = int(shift_time.split(":")[0])  # Get the hour part of the shift start time
    day_index = shift_hour % 7  # Just an example logic to cycle through days
    return day_of_week[day_index]


def generate_initial_population(population_size, nurses, shift_time):
    population = []
    for _ in range(population_size):
        schedule = []
        for nurse in nurses:
            shift = random.choice(shift_time)  # Assign random shift time for the nurse
            schedule.append((nurse[0], shift))  # nurse[0] is nurse_id
        population.append(schedule)
    return population

def fitness_function(schedule, nurses, shift_time):
    violations = 0
    for nurse_id, shift in schedule:
        # Example of constraint check (e.g., shift preference match)
        nurse = next(n for n in nurses if n[0] == nurse_id)
        if nurse[2] != shift:  # If nurse's preference does not match the assigned shift
            violations += 1
    return violations

def crossover(parent1, parent2):
    crossover_point = len(parent1) // 2
    child = parent1[:crossover_point] + parent2[crossover_point:]
    return child

def mutate(schedule, shift_time):
    mutation_point = random.randint(0, len(schedule) - 1)
    nurse_id, _ = schedule[mutation_point]
    new_shift = random.choice(shift_time)
    schedule[mutation_point] = (nurse_id, new_shift)
    return schedule

def genetic_algorithm(nurses, shift_time, population_size=10, generations=100, mutation_rate=0.1):
    population = generate_initial_population(population_size, nurses, shift_time)
    
    for generation in range(generations):
        # Sort population by fitness (lower fitness is better)
        population = sorted(population, key=lambda schedule: fitness_function(schedule, nurses, shift_time))

        # Elitism: Keep the best 2 individuals
        next_generation = population[:2]

        # Crossover and mutation to create new individuals
        while len(next_generation) < population_size:
            parent1, parent2 = random.choices(population[:5], k=2)  # Select from top 5
            child = crossover(parent1, parent2)

            if random.random() < mutation_rate:
                child = mutate(child, shift_time)

            next_generation.append(child)

        population = next_generation
    
    # Best schedule is the first in the sorted population
    best_schedule = population[0]
    return best_schedule

def get_shift_end_time(shift_start):
    # Assuming shifts are of fixed duration
    shift_end_map = {
        '08:00:00': '16:00:00',  # Morning shift
        '16:00:00': '00:00:00',  # Afternoon shift
        '00:00:00': '08:00:00'   # Night shift
    }
    return shift_end_map.get(shift_start, 'Unknown')

# Generate schedule route
# Define the route to generate the schedule
@admin_bp.route('/generate_schedule', methods=['GET', 'POST'])
def generate_schedule():
    if 'user_id' not in session:
        flash('You need to log in first!', 'error')
        return redirect(url_for('auth.login'))

    schedule = None

    if request.method == 'POST':
        # Get form data
        num_nurses_per_shift = int(request.form.get('num_nurses_per_shift'))
        category_filter = request.form.get('category_filter')
        max_days_per_week = int(request.form.get('max_days_per_week'))
        shift_preference = request.form.get('shift_preference')
        shift_time = request.form.getlist('shift_time')  # List of shift times selected

        # Query nurses based on constraints (e.g., category_filter)
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Modify the query if you want to filter based on category or shift preference
        cur.execute("SELECT nurse_id, name, shift_preference FROM nurses WHERE category = %s", (category_filter,))
        nurses = cur.fetchall()

        # Check if the data is being fetched correctly
        print(f"Nurses: {nurses}")
        
        # Generate the schedule using the genetic algorithm
        best_schedule = genetic_algorithm(nurses, shift_time, population_size=num_nurses_per_shift)

        # Prepare the schedule data for each day of the week
        weekly_schedule = {
            "Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [],
            "Friday": [], "Saturday": [], "Sunday": []
        }

        for nurse_id, shift in best_schedule:
            # Find the nurse and shift preference
            nurse = next(n for n in nurses if n[0] == nurse_id)
            preferred_shift = nurse[2]  # Assuming the preference is stored as Morning, Afternoon, or Night
            
            if shift_preference == 'Any' or shift == shift_preference:
                # Add the nurse to the correct shift for the corresponding day
                day_of_week = random.choice(list(weekly_schedule.keys()))  # You can change this logic as needed
                weekly_schedule[day_of_week].append((nurse[1], shift))  # (Nurse Name, Shift)

        # Save the schedule to the database
        for day, shifts in weekly_schedule.items():
            for nurse_name, shift in shifts:
                cur.execute("""
                    INSERT INTO schedules (nurse_id, shift_day, shift_start, shift_end, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nurse_id, day, shift, get_shift_end_time(shift), "Scheduled"))

        conn.commit()

        # Fetch the generated schedule to display
        cur.execute("""
            SELECT s.schedule_id, n.name, s.shift_day, s.shift_start, s.shift_end, s.status
            FROM schedules s
            JOIN nurses n ON s.nurse_id = n.nurse_id
            WHERE s.status = 'Scheduled'
        """)
        schedule = cur.fetchall()

        cur.close()
        conn.close()

        flash('Schedule generated successfully!', 'success')

    return render_template('admin/generate_schedule.html', schedule=schedule)

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

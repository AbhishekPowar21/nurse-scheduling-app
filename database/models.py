# models.py

from . import get_db_connection

def create_hospital_admin_table():
    """
    Creates the hospital_admin table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hospital_admin (
        admin_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        hospital_name VARCHAR(100) NOT NULL,
        hospital_address VARCHAR(200) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)
    connection.commit()
    cursor.close()
    connection.close()

def create_nurses_table():
    """
    Creates the nurses table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nurses (
        nurse_id INT AUTO_INCREMENT PRIMARY KEY,
        admin_id INT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        phone VARCHAR(15) NOT NULL,
        shift_preference VARCHAR(100),
        sleep_hours INT NOT NULL,
        category ENUM('Senior', 'Junior', 'Head') NOT NULL,
        department VARCHAR(100) NOT NULL,
        status ENUM('Active', 'Inactive') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES hospital_admin(admin_id)
    )
    """)
    connection.commit()
    cursor.close()
    connection.close()

def create_schedules_table():
    """
    Creates the schedules table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        schedule_id INT AUTO_INCREMENT PRIMARY KEY,
        nurse_id INT,
        shift_day VARCHAR(20) NOT NULL,
        shift_start TIME NOT NULL,
        shift_end TIME NOT NULL,
        break_start TIME,
        break_end TIME,
        backup_schedule BOOLEAN DEFAULT FALSE,
        status ENUM('Scheduled', 'Backup', 'Pending') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
    )
    """)
    connection.commit()
    cursor.close()
    connection.close()

def create_schedule_accuracy_table():
    """
    Creates the schedule_accuracy table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_accuracy (
        accuracy_id INT AUTO_INCREMENT PRIMARY KEY,
        schedule_id INT,
        constraint_violations INT NOT NULL,
        accuracy_percentage DECIMAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id)
    )
    """)
    connection.commit()
    cursor.close()
    connection.close()

def create_shift_preferences_table():
    """
    Creates the shift_preferences table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shift_preferences (
        preference_id INT AUTO_INCREMENT PRIMARY KEY,
        nurse_id INT,
        preferred_shift_start TIME NOT NULL,
        preferred_shift_end TIME NOT NULL,
        preferred_days VARCHAR(100),
        FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
    )
    """)
    connection.commit()
    cursor.close()
    connection.close()

def create_constraints_table():
    """
    Creates the constraints table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS constraints (
        constraint_id INT AUTO_INCREMENT PRIMARY KEY,
        nurse_id INT,
        constraint_type ENUM('Sleep Hours', 'Max Shifts') NOT NULL,
        value INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
    )
    """)
    connection.commit()
    cursor.close()
    connection.close()

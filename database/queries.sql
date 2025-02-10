-- Step 1: Create the Database
CREATE DATABASE nurse_scheduling;

-- Step 2: Use the newly created database
USE nurse_scheduling;

-- Step 3: Create the 'constraints' table
CREATE TABLE constraints (
    constraint_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT NOT NULL,
    constraint_type ENUM('Sleep Hours', 'Max Shifts') NOT NULL,
    value INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

-- Step 4: Create the 'hospital_admin' table
CREATE TABLE hospital_admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(100) NOT NULL,
    hospital_address VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Step 5: Create the 'nurse_schedule' table
CREATE TABLE nurse_schedule (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    nurse_id INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    shift ENUM('Morning', 'Evening', 'Night') NOT NULL,
    shift_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES hospital_admin(admin_id),
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

-- Step 6: Create the 'nurses' table
CREATE TABLE nurses (
    nurse_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL,
    shift_preference VARCHAR(100),
    sleep_hours INT NOT NULL,
    category ENUM('Senior', 'Junior', 'Head') NOT NULL,
    department VARCHAR(100) NOT NULL,
    status ENUM('Active', 'Inactive') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES hospital_admin(admin_id)
);

-- Step 7: Create the 'schedules' table
CREATE TABLE schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT NOT NULL,
    shift_day VARCHAR(20),
    shift_start VARCHAR(20),
    shift_end VARCHAR(20),
    status ENUM('Scheduled', 'Backup', 'Pending') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

-- Step 8: Create the 'schedule_accuracy' table
CREATE TABLE schedule_accuracy (
    accuracy_id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    constraint_violations INT NOT NULL,
    accuracy_percentage DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id)
);

-- Step 9: Create the 'shift_preferences' table
CREATE TABLE shift_preferences (
    preference_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT NOT NULL,
    preferred_shift_start TIME NOT NULL,
    preferred_shift_end TIME NOT NULL,
    preferred_days ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

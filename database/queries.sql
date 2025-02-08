CREATE TABLE hospital_admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(100) NOT NULL,
    hospital_address VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE nurses (
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
);

CREATE TABLE schedules (
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
);

CREATE TABLE schedule_accuracy (
    accuracy_id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT,
    constraint_violations INT NOT NULL,
    accuracy_percentage DECIMAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id)
);

CREATE TABLE shift_preferences (
    preference_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT,
    preferred_shift_start TIME NOT NULL,
    preferred_shift_end TIME NOT NULL,
    preferred_days VARCHAR(100),
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

CREATE TABLE constraints (
    constraint_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT,
    constraint_type ENUM('Sleep Hours', 'Max Shifts') NOT NULL,
    value INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id)
);

latest one 

-- Create hospital_admin table
CREATE TABLE hospital_admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(100) NOT NULL,
    hospital_address VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create nurses table
CREATE TABLE nurses (
    nurse_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
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
    FOREIGN KEY (admin_id) REFERENCES hospital_admin(admin_id) ON DELETE CASCADE
);

-- Create schedules table
CREATE TABLE schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT NOT NULL,
    shift_day ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    shift_start TIME NOT NULL,
    shift_end TIME NOT NULL,
    break_start TIME,
    break_end TIME,
    backup_schedule BOOLEAN DEFAULT FALSE,
    status ENUM('Scheduled', 'Backup', 'Pending') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id) ON DELETE CASCADE
);

-- Create schedule_accuracy table
CREATE TABLE schedule_accuracy (
    accuracy_id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    constraint_violations INT NOT NULL,
    accuracy_percentage DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id) ON DELETE CASCADE
);

-- Create shift_preferences table
CREATE TABLE shift_preferences (
    preference_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT NOT NULL,
    preferred_shift_start TIME NOT NULL,
    preferred_shift_end TIME NOT NULL,
    preferred_days ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id) ON DELETE CASCADE
);

-- Create constraints table
CREATE TABLE constraints (
    constraint_id INT AUTO_INCREMENT PRIMARY KEY,
    nurse_id INT NOT NULL,
    constraint_type ENUM('Sleep Hours', 'Max Shifts') NOT NULL,
    value INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nurse_id) REFERENCES nurses(nurse_id) ON DELETE CASCADE
);

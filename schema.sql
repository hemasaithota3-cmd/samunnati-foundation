-- Samunnathi database schema (MySQL 8+)
-- Run: mysql -u root -p < schema.sql
-- Or let SQLAlchemy create tables automatically via `flask shell` / app startup
-- (db.create_all()) - this file is provided for manual setup, migrations, and
-- as a reference for the exact structure.

CREATE DATABASE IF NOT EXISTS samunnathi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE samunnathi;

-- ------------------------------------------------------------------ admins
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active_admin BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------ guidance_requests
CREATE TABLE IF NOT EXISTS guidance_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_number VARCHAR(20) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(190) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    education_level VARCHAR(120) NOT NULL,
    institution VARCHAR(200) NULL,
    location VARCHAR(150) NOT NULL,
    guidance_area VARCHAR(60) NOT NULL,
    preferred_contact VARCHAR(30) NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_guidance_email (email),
    INDEX idx_guidance_reference (reference_number),
    INDEX idx_guidance_status (status),
    INDEX idx_guidance_created (created_at),
    INDEX idx_guidance_is_read (is_read)
) ENGINE=InnoDB;

-- ------------------------------------------------------------ mentor_applications
CREATE TABLE IF NOT EXISTS mentor_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_number VARCHAR(20) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(190) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    location VARCHAR(150) NOT NULL,
    qualification VARCHAR(150) NOT NULL,
    profession VARCHAR(150) NOT NULL,
    organization VARCHAR(200) NULL,
    years_experience VARCHAR(30) NULL,
    expertise TEXT NOT NULL,
    mentoring_areas TEXT NOT NULL,
    availability VARCHAR(60) NOT NULL,
    linkedin VARCHAR(255) NULL,
    portfolio VARCHAR(255) NULL,
    reason TEXT NOT NULL,
    message TEXT NULL,
    resume_original_name VARCHAR(255) NOT NULL,
    resume_stored_name VARCHAR(255) NOT NULL UNIQUE,
    resume_path VARCHAR(500) NOT NULL,
    resume_uploaded_at DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_mentor_email (email),
    INDEX idx_mentor_reference (reference_number),
    INDEX idx_mentor_status (status),
    INDEX idx_mentor_created (created_at),
    INDEX idx_mentor_is_read (is_read)
) ENGINE=InnoDB;

-- ------------------------------------------------------------ volunteer_applications
CREATE TABLE IF NOT EXISTS volunteer_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_number VARCHAR(20) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(190) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    location VARCHAR(150) NOT NULL,
    education_profession VARCHAR(200) NULL,
    skills TEXT NOT NULL,
    areas_of_interest TEXT NOT NULL,
    availability VARCHAR(60) NOT NULL,
    previous_experience TEXT NULL,
    reason TEXT NOT NULL,
    message TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_volunteer_email (email),
    INDEX idx_volunteer_reference (reference_number),
    INDEX idx_volunteer_status (status),
    INDEX idx_volunteer_created (created_at),
    INDEX idx_volunteer_is_read (is_read)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------ notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message VARCHAR(500) NOT NULL,
    reference_id INT NOT NULL,
    application_type VARCHAR(20) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notifications_is_read (is_read),
    INDEX idx_notifications_created (created_at),
    INDEX idx_notifications_app_ref (application_type, reference_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------- email_logs
CREATE TABLE IF NOT EXISTS email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_type VARCHAR(20) NOT NULL,
    application_id INT NOT NULL,
    recipient VARCHAR(190) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    kind VARCHAR(30) NOT NULL DEFAULT 'confirmation',
    status VARCHAR(20) NOT NULL DEFAULT 'SENT',
    error_message VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_logs_app (application_type, application_id)
) ENGINE=InnoDB;

-- AI Speech Coach Database Schema
-- MySQL Database

-- Create database
CREATE DATABASE IF NOT EXISTS speech_coach CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE speech_coach;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_firebase_uid (firebase_uid),
    INDEX idx_email (email)
);

-- Sessions table
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    goal ENUM('reduce_fillers', 'improve_fluency', 'interview_practice', 'presentation_practice') NOT NULL,
    context TEXT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_start_time (start_time),
    INDEX idx_goal (goal)
);

-- Session metrics table
CREATE TABLE session_metrics (
    session_id INT PRIMARY KEY,
    wpm FLOAT NOT NULL COMMENT 'Words per minute',
    filler_count INT NOT NULL,
    filler_ratio FLOAT NOT NULL COMMENT 'Ratio of filler words to total words',
    avg_pause FLOAT NOT NULL COMMENT 'Average pause duration in seconds',
    pitch_variance FLOAT NOT NULL,
    confidence_score FLOAT NOT NULL,
    emotion_label VARCHAR(50) NOT NULL,
    goal_score FLOAT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_goal_score (goal_score),
    INDEX idx_emotion_label (emotion_label)
);

-- Additional indexes for performance
CREATE INDEX idx_sessions_user_start ON sessions(user_id, start_time DESC);
CREATE INDEX idx_metrics_confidence ON session_metrics(confidence_score DESC);

-- Sample data for testing (optional)
-- INSERT INTO users (firebase_uid, email) VALUES 
-- ('test_uid_123', 'test@example.com');

-- INSERT INTO sessions (user_id, goal, context) VALUES 
-- (1, 'improve_fluency', 'Practice session for presentation skills');

-- INSERT INTO session_metrics (session_id, wpm, filler_count, filler_ratio, avg_pause, pitch_variance, confidence_score, emotion_label, goal_score) VALUES 
-- (1, 145.5, 3, 0.05, 2.3, 180.2, 0.75, 'confident', 0.78);

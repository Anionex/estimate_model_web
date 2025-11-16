-- 创建数据库
CREATE DATABASE IF NOT EXISTS modeltest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE modeltest;

-- ModelEstimate表
CREATE TABLE IF NOT EXISTS ModelEstimate (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question VARCHAR(2000),
    gpt_response VARCHAR(4000),
    gpt_overall_rating INT,
    gpt_route_rationality_rating INT,
    gpt_representativeness_rating INT,
    trip_response VARCHAR(4000),
    trip_overall_rating INT,
    trip_route_rationality_rating INT,
    trip_representativeness_rating INT,
    our_response VARCHAR(4000),
    our_overall_rating INT,
    our_route_rationality_rating INT,
    our_representativeness_rating INT,
    feedback VARCHAR(2000),
    create_time DATETIME
);

-- User表
CREATE TABLE IF NOT EXISTS User (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Feedback表
CREATE TABLE IF NOT EXISTS Feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    model_estimate_id INT,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id),
    FOREIGN KEY (model_estimate_id) REFERENCES ModelEstimate(id)
);

-- Session表
CREATE TABLE IF NOT EXISTS Session (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(id)
);

-- Log表
-- Log表（续）
CREATE TABLE IF NOT EXISTS Log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    level ENUM('INFO', 'WARNING', 'ERROR') NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_modelestimate_create_time ON ModelEstimate(create_time);
CREATE INDEX idx_user_username ON User(username);
CREATE INDEX idx_user_email ON User(email);
CREATE INDEX idx_feedback_user_id ON Feedback(user_id);
CREATE INDEX idx_feedback_model_estimate_id ON Feedback(model_estimate_id);
CREATE INDEX idx_session_user_id ON Session(user_id);
CREATE INDEX idx_session_token ON Session(token);
CREATE INDEX idx_log_level ON Log(level);
CREATE INDEX idx_log_created_at ON Log(created_at);

-- 设置字符集和排序规则
ALTER DATABASE modeltest CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
ALTER TABLE ModelEstimate CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE User CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE Feedback CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE Session CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE Log CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE model_estimate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question VARCHAR(2000),
    gpt_response VARCHAR(4000),
    gpt_overall_rating INT,
    gpt_route_rationality_rating INT,
    gpt_representativeness_rating INT,
    trip_response VARCHAR(4000),
    trip_overall_rating INT,
    trip_route_rationality_rating INT,
    trip_representativeness_rating INT,
    our_response VARCHAR(4000),
    our_overall_rating INT,
    our_route_rationality_rating INT,
    our_representativeness_rating INT,
    feedback VARCHAR(2000),
    create_time DATETIME
);
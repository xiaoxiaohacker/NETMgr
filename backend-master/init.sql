-- NetMgr 数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS netmgr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE netmgr;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建设备表
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    management_ip VARCHAR(45) UNIQUE NOT NULL,
    vendor VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    os_version VARCHAR(100),
    serial_number VARCHAR(100),
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    enable_password VARCHAR(255),
    port INT DEFAULT 22,
    device_type VARCHAR(50),
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'unknown',
    owner_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- 创建接口状态表
CREATE TABLE IF NOT EXISTS interface_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    interface_name VARCHAR(50) NOT NULL,
    admin_status VARCHAR(20),
    operational_status VARCHAR(20),
    mac_address VARCHAR(17),
    connected_to_mac VARCHAR(17),
    ip_address VARCHAR(45),
    speed VARCHAR(20),
    description VARCHAR(255),
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- 创建配置备份表
CREATE TABLE IF NOT EXISTS configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    config TEXT NOT NULL,
    taken_by VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    file_size INT DEFAULT 0,
    hash VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- 创建命令日志表
CREATE TABLE IF NOT EXISTS command_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    command TEXT NOT NULL,
    output TEXT,
    executed_by VARCHAR(50) NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- 创建告警表
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT,
    alert_type VARCHAR(50) NOT NULL,
    severity ENUM('Critical', 'Major', 'Minor', 'Warning') DEFAULT 'Warning',
    message TEXT,
    status ENUM('New', 'Acknowledged', 'Resolved') DEFAULT 'New',
    acknowledged_at TIMESTAMP NULL,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    task_type ENUM('config_backup', 'config_restore', 'firmware_update', 'reboot') NOT NULL,
    status ENUM('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    scheduled_time TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    logs TEXT,
    progress INT DEFAULT 0
);

-- 创建系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);

-- 创建初始管理员用户 (密码: admin123)
-- 注意：这是加密后的密码，明文为 'admin123'
INSERT IGNORE INTO users (id, username, email, hashed_password, is_active) VALUES
(1, 'admin', 'admin@example.com', '$2b$12$LQYxq.L6o/z4T2yZ7TLg.eHk/VSmXEEO/5Wj1F/8yZJiF7UxHCr3C', TRUE);
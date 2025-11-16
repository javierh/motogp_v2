-- NovaPorra Database Schema
-- MySQL 8.0+

-- Users table (Telegram users)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_telegram_id (telegram_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Categories table (MotoGP, Moto2, Moto3)
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default categories
INSERT INTO categories (name, code) VALUES
    ('MotoGP', 'MOTOGP'),
    ('Moto2', 'MOTO2'),
    ('Moto3', 'MOTO3')
ON DUPLICATE KEY UPDATE name=name;

-- Circuits table
CREATE TABLE IF NOT EXISTS circuits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    external_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_external_id (external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Grand Prix events
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    season INT NOT NULL,
    circuit_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    external_id VARCHAR(100) UNIQUE,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (circuit_id) REFERENCES circuits(id) ON DELETE CASCADE,
    INDEX idx_season (season),
    INDEX idx_event_date (event_date),
    INDEX idx_external_id (external_id),
    INDEX idx_is_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Race types (sprint, race)
CREATE TABLE IF NOT EXISTS race_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    points_exact_position INT NOT NULL COMMENT 'Points for exact rider + position match',
    points_rider_only INT NOT NULL COMMENT 'Points for correct rider but wrong position',
    points_perfect_podium INT NOT NULL COMMENT 'Bonus points for perfect podium (all 3 correct)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert race types with new scoring system
-- 10 points for exact match, 5 for rider in podium, +10 bonus for perfect podium
INSERT INTO race_types (name, code, points_exact_position, points_rider_only, points_perfect_podium) VALUES
    ('Sprint Race', 'SPRINT', 10, 5, 10),
    ('Main Race', 'RACE', 10, 5, 10)
ON DUPLICATE KEY UPDATE name=name;

-- Races (specific race for each category in an event)
CREATE TABLE IF NOT EXISTS races (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    category_id INT NOT NULL,
    race_type_id INT NOT NULL,
    race_datetime DATETIME NOT NULL,
    bet_close_datetime DATETIME NOT NULL,
    status ENUM('upcoming', 'betting_open', 'betting_closed', 'in_progress', 'finished', 'cancelled') DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (race_type_id) REFERENCES race_types(id) ON DELETE CASCADE,
    UNIQUE KEY unique_race (event_id, category_id, race_type_id),
    INDEX idx_race_datetime (race_datetime),
    INDEX idx_status (status),
    INDEX idx_bet_close (bet_close_datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Riders table
CREATE TABLE IF NOT EXISTS riders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    number INT,
    country VARCHAR(100),
    external_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_external_id (external_id),
    INDEX idx_number (number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rider season participation (which category they race in each season)
CREATE TABLE IF NOT EXISTS rider_seasons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rider_id INT NOT NULL,
    category_id INT NOT NULL,
    season INT NOT NULL,
    team_name VARCHAR(200),
    bike VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rider_season (rider_id, category_id, season),
    INDEX idx_season (season),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User bets
CREATE TABLE IF NOT EXISTS bets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    race_id INT NOT NULL,
    first_place_rider_id INT NOT NULL,
    second_place_rider_id INT NOT NULL,
    third_place_rider_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    FOREIGN KEY (first_place_rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    FOREIGN KEY (second_place_rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    FOREIGN KEY (third_place_rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_race_bet (user_id, race_id),
    INDEX idx_race_id (race_id),
    INDEX idx_user_id (user_id),
    CHECK (first_place_rider_id != second_place_rider_id 
           AND first_place_rider_id != third_place_rider_id 
           AND second_place_rider_id != third_place_rider_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Race results
CREATE TABLE IF NOT EXISTS race_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    race_id INT NOT NULL,
    rider_id INT NOT NULL,
    position INT NOT NULL,
    points INT DEFAULT 0,
    time_gap VARCHAR(50),
    status ENUM('finished', 'dnf', 'dns', 'dsq') DEFAULT 'finished',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    UNIQUE KEY unique_race_position (race_id, position),
    INDEX idx_race_id (race_id),
    INDEX idx_rider_id (rider_id),
    INDEX idx_position (position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User scores from bets
CREATE TABLE IF NOT EXISTS bet_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bet_id INT NOT NULL,
    race_id INT NOT NULL,
    user_id INT NOT NULL,
    points_first INT DEFAULT 0 COMMENT 'Points from first position prediction',
    points_second INT DEFAULT 0 COMMENT 'Points from second position prediction',
    points_third INT DEFAULT 0 COMMENT 'Points from third position prediction',
    perfect_podium_bonus INT DEFAULT 0 COMMENT 'Bonus points for perfect podium',
    total_points INT DEFAULT 0 COMMENT 'Total points (sum of all)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bet_id) REFERENCES bets(id) ON DELETE CASCADE,
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_bet_score (bet_id),
    INDEX idx_race_id (race_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Session types (FP1, FP2, Q1, Q2, etc.)
CREATE TABLE IF NOT EXISTS session_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO session_types (name, code) VALUES
    ('Free Practice 1', 'FP1'),
    ('Free Practice 2', 'FP2'),
    ('Free Practice 3', 'FP3'),
    ('Qualifying 1', 'Q1'),
    ('Qualifying 2', 'Q2'),
    ('Warm Up', 'WUP')
ON DUPLICATE KEY UPDATE name=name;

-- Practice/Qualifying sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    race_id INT NOT NULL,
    session_type_id INT NOT NULL,
    session_datetime DATETIME NOT NULL,
    status ENUM('scheduled', 'in_progress', 'finished', 'cancelled') DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    FOREIGN KEY (session_type_id) REFERENCES session_types(id) ON DELETE CASCADE,
    INDEX idx_race_id (race_id),
    INDEX idx_session_datetime (session_datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Session results (lap times, positions)
CREATE TABLE IF NOT EXISTS session_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    rider_id INT NOT NULL,
    position INT,
    best_lap_time VARCHAR(20),
    best_lap_number INT,
    total_laps INT,
    gap_to_first VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    UNIQUE KEY unique_session_rider (session_id, rider_id),
    INDEX idx_session_id (session_id),
    INDEX idx_position (position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Championship standings by category
CREATE TABLE IF NOT EXISTS championship_standings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    season INT NOT NULL,
    category_id INT NOT NULL,
    user_id INT NOT NULL,
    total_points INT DEFAULT 0,
    races_participated INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_season_category_user (season, category_id, user_id),
    INDEX idx_season (season),
    INDEX idx_category_points (category_id, total_points DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Global championship standings (all categories combined)
CREATE TABLE IF NOT EXISTS global_standings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    season INT NOT NULL,
    user_id INT NOT NULL,
    total_points INT DEFAULT 0,
    motogp_points INT DEFAULT 0,
    moto2_points INT DEFAULT 0,
    moto3_points INT DEFAULT 0,
    races_participated INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_season_user (season, user_id),
    INDEX idx_season (season),
    INDEX idx_total_points (total_points DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notifications log
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_type ENUM('bet_closing', 'bet_closed', 'race_result', 'standings_update') NOT NULL,
    race_id INT,
    message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE SET NULL,
    INDEX idx_notification_type (notification_type),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

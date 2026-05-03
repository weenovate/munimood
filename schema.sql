-- ============================================================
-- MuniMood - Termómetro Político Municipal
-- Esquema de Base de Datos MySQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS munimood CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE munimood;

-- ------------------------------------------------------------
-- Usuarios del sistema
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_admin TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Sesiones activas (tokens JWT almacenados para revocación)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Tokens para restablecer contraseña
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    used TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Ejes / Temas del termómetro
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS topics (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    icon VARCHAR(60) DEFAULT 'bi-circle',
    display_order INT UNSIGNED NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Fuentes de información (perfiles de redes sociales)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS information_sources (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    social_network ENUM('facebook','instagram','twitter') NOT NULL,
    profile_handle VARCHAR(255),
    start_date DATE NOT NULL,
    refresh_rate ENUM('30min','1h','4h','12h','24h','never') NOT NULL DEFAULT 'never',
    refresh_window ENUM('24h','48h','72h','1week') DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_scraped_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Posteos relevados
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_id INT UNSIGNED NOT NULL,
    topic_id INT UNSIGNED DEFAULT NULL,
    external_id VARCHAR(255),
    title VARCHAR(1024),
    content TEXT,
    post_url VARCHAR(2048),
    post_date DATETIME,
    positive_comments INT UNSIGNED NOT NULL DEFAULT 0,
    negative_comments INT UNSIGNED NOT NULL DEFAULT 0,
    neutral_comments INT UNSIGNED NOT NULL DEFAULT 0,
    last_refreshed_at DATETIME DEFAULT NULL,
    next_refresh_at DATETIME DEFAULT NULL,
    refresh_until DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES information_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL,
    INDEX idx_source_id (source_id),
    INDEX idx_topic_id (topic_id),
    INDEX idx_post_date (post_date),
    INDEX idx_next_refresh (next_refresh_at),
    UNIQUE KEY uq_source_external (source_id, external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Comentarios de los posteos
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    post_id INT UNSIGNED NOT NULL,
    external_id VARCHAR(255),
    content TEXT NOT NULL,
    sentiment ENUM('positive','negative','neutral') NOT NULL DEFAULT 'neutral',
    sentiment_score FLOAT DEFAULT 0,
    author VARCHAR(255),
    comment_date DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    INDEX idx_post_id (post_id),
    INDEX idx_sentiment (sentiment),
    UNIQUE KEY uq_post_external (post_id, external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Configuración del semáforo (escala de % por color)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS traffic_light_config (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    green_min_pct FLOAT NOT NULL DEFAULT 61.0,
    yellow_min_pct FLOAT NOT NULL DEFAULT 31.0,
    yellow_max_pct FLOAT NOT NULL DEFAULT 60.0,
    red_max_pct FLOAT NOT NULL DEFAULT 30.0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Configuración general de la aplicación (clave-valor)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Log de scraping
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scraping_logs (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_id INT UNSIGNED,
    status ENUM('running','success','error','partial') NOT NULL DEFAULT 'running',
    posts_found INT UNSIGNED DEFAULT 0,
    comments_found INT UNSIGNED DEFAULT 0,
    message TEXT,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME DEFAULT NULL,
    FOREIGN KEY (source_id) REFERENCES information_sources(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

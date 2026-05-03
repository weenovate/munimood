-- ============================================================
-- MuniMood - Datos iniciales
-- ============================================================
USE munimood;

-- Usuario inicial: muniadmin / Ramallo2026
-- Hash bcrypt generado por el script de inicialización
-- Se reemplaza automáticamente al ejecutar: python backend/init_db.py
INSERT IGNORE INTO users (username, email, password_hash, full_name, is_active, is_admin)
VALUES (
    'muniadmin',
    'admin@municipio.gob.ar',
    '$2b$12$PLACEHOLDER_HASH_DO_NOT_USE_RUN_INIT_DB',
    'Administrador Municipal',
    1,
    1
);

-- Ejes temáticos por defecto
INSERT IGNORE INTO topics (name, icon, display_order, is_active) VALUES
('Economía',       'bi-graph-up-arrow',   1, 1),
('Desarrollo',     'bi-buildings',        2, 1),
('Seguridad',      'bi-shield-check',     3, 1),
('Obras Públicas', 'bi-cone-striped',     4, 1),
('Educación',      'bi-mortarboard',      5, 1),
('Salud',          'bi-heart-pulse',      6, 1),
('Turismo',        'bi-map',              7, 1),
('Medio Ambiente', 'bi-tree',             8, 1),
('Entretenimiento','bi-music-note-beamed',9, 1);

-- Configuración semáforo por defecto
INSERT IGNORE INTO traffic_light_config (id, green_min_pct, yellow_min_pct, yellow_max_pct, red_max_pct)
VALUES (1, 61.0, 31.0, 60.0, 30.0);

-- Configuración AI por defecto
INSERT IGNORE INTO app_config (config_key, config_value) VALUES
('ai_engine', 'local'),
('ai_api_key', ''),
('ai_model', ''),
('smtp_configured', 'false');

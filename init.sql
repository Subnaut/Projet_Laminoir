-- Création de la base de données du projet Cage Laminoir
CREATE DATABASE IF NOT EXISTS laminoir
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE laminoir;

-- Table de référence des cages de laminage
CREATE TABLE IF NOT EXISTS cages (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    nom  VARCHAR(50) NOT NULL UNIQUE
);

-- Table des mesures (température / vibration) relevées par cage
CREATE TABLE IF NOT EXISTS mesures (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    cage_id      INT NOT NULL,
    date_mesure  DATETIME NOT NULL,
    temperature  INT NOT NULL,
    vibration    DECIMAL(5,2) NOT NULL,
    CONSTRAINT fk_mesures_cage
        FOREIGN KEY (cage_id) REFERENCES cages(id)
        ON DELETE CASCADE,
    UNIQUE KEY uq_cage_date (cage_id, date_mesure)
);

CREATE INDEX idx_mesures_date ON mesures (date_mesure);

-- Initialisation des 6 cages du laminoir
INSERT IGNORE INTO cages (nom) VALUES
    ('cage1'), ('cage2'), ('cage3'), ('cage4'), ('cage5'), ('cage6');

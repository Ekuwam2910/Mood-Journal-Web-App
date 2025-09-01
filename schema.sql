-- MySQL schema (if you prefer manual creation)
CREATE TABLE IF NOT EXISTS entries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  text TEXT NOT NULL,
  mood_label VARCHAR(32) NOT NULL,
  mood_score FLOAT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

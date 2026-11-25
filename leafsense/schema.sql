CREATE DATABASE IF NOT EXISTS leafsense CHARACTER SET utf8mb4;
USE leafsense;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  name VARCHAR(80) NOT NULL,
  species VARCHAR(80),
  is_control BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_features (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plant_id INT NOT NULL,
  photo_date DATE NOT NULL,
  image_path VARCHAR(255) NOT NULL,
  green_area_px DOUBLE, green_area_pct DOUBLE,
  mean_R DOUBLE, mean_G DOUBLE, mean_B DOUBLE,
  mean_H DOUBLE, mean_S DOUBLE, mean_V DOUBLE,
  exg_mean DOUBLE, greenness_ratio DOUBLE, yellow_pct DOUBLE,
  stress_pred TINYINT DEFAULT 0,
  UNIQUE KEY uq_plant_date (plant_id, photo_date),
  FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plant_id INT NOT NULL,
  alert_date DATE NOT NULL,
  message VARCHAR(255),
  UNIQUE KEY uq_alert (plant_id, alert_date),
  FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
);

-- Labels for training/evaluation (Step 2 data collection)
CREATE TABLE IF NOT EXISTS plant_events (
  plant_id INT PRIMARY KEY,
  stress_onset DATE,
  first_visible_symptom DATE,
  FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
);

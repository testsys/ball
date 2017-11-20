CREATE DATABASE `ball`;
CREATE USER 'ball'@'localhost' IDENTIFIED BY 'password';
CREATE USER 'ball_admin'@'localhost' IDENTIFIED BY 'very_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON `ball`.* TO 'ball'@'localhost';
GRANT ALL ON `ball`.* TO 'ball_admin'@'localhost';
FLUSH PRIVILEGES;

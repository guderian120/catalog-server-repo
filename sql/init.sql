-- Create the database
CREATE DATABASE IF NOT EXISTS catalog;

-- Use the database
USE catalog;

-- Create the products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL
);

-- Insert sample data
INSERT INTO products (name, description, price) VALUES
('Laptop', 'A high-end laptop', 1200.00),
('Phone', 'Latest smartphone', 800.00);

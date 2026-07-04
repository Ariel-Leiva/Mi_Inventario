-- Create users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);

-- Create products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    buy_price REAL NOT NULL, -- Purchase cost
    sell_price REAL NOT NULL, -- Selling price
    stock INTEGER NOT NULL DEFAULT 0,
    min_stock INTEGER NOT NULL DEFAULT 5, -- Low stock threshold
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create sales table
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_price REAL NOT NULL, -- sell_price * quantity
    profit REAL NOT NULL, -- (sell_price - buy_price) * quantity
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

-- Create indexes for performance
CREATE INDEX idx_products_user ON products(user_id);
CREATE INDEX idx_sales_user ON sales(user_id);
CREATE INDEX idx_sales_product ON sales(product_id);

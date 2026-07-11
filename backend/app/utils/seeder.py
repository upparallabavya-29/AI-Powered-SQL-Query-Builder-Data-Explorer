import sqlite3
import random
from datetime import datetime, timedelta

def seed_sample_database(db_path: str):
    """
    Seeds the target SQLite database with sample tables and a high-fidelity analytics dataset
    containing customers, products, employees, orders, and sales.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create Tables
    cursor.execute("DROP TABLE IF EXISTS sales")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS employees")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS customers")

    cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            country VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock INT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            department VARCHAR(50) NOT NULL,
            salary DECIMAL(10, 2) NOT NULL,
            hire_date DATE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INT NOT NULL,
            employee_id INT,
            order_date TIMESTAMP NOT NULL,
            status VARCHAR(20) NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            discount DECIMAL(5, 2) DEFAULT 0.00,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 2. Seed Data
    # 2.1 Seed Customers (20 customers)
    countries = ["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan"]
    customer_names = [
        "Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Evan Wright",
        "Fiona Gallagher", "George Clark", "Hannah Abbott", "Ian Malcolm", "Julia Roberts",
        "Kevin Bacon", "Laura Croft", "Michael Scott", "Nancy Drew", "Oscar Wilde",
        "Penelope Cruz", "Quentin Tarantino", "Rachel Green", "Steve Rogers", "Tony Stark"
    ]
    customers = []
    for i, name in enumerate(customer_names, 1):
        email = f"{name.lower().replace(' ', '.')}@example.com"
        country = random.choice(countries)
        created_days_ago = random.randint(10, 365)
        created_at = (datetime.utcnow() - timedelta(days=created_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO customers (name, email, country, created_at) VALUES (?, ?, ?, ?)",
            (name, email, country, created_at)
        )
        customers.append(i)

    # 2.2 Seed Products (15 products)
    product_catalog = [
        ("UltraBook Pro 15", "Electronics", 1299.99, 50),
        ("NoiseCancelling Headphones", "Electronics", 299.99, 120),
        ("SmartWatch Series 5", "Electronics", 399.99, 80),
        ("HD Webcam 1080p", "Electronics", 79.99, 150),
        ("Ergonomic Office Chair", "Furniture", 249.99, 30),
        ("Standing Desk Dual-Motor", "Furniture", 499.99, 15),
        ("LED Desk Lamp", "Furniture", 39.99, 200),
        ("Stainless Steel Water Bottle", "Home & Kitchen", 24.99, 300),
        ("Coffee Maker with Grinder", "Home & Kitchen", 189.99, 45),
        ("Air Fryer XL", "Home & Kitchen", 149.99, 60),
        ("Running Shoes Zoom", "Apparel", 120.00, 100),
        ("Waterproof Backpack", "Apparel", 59.99, 180),
        ("Bluetooth Speaker Outdoor", "Electronics", 89.99, 90),
        ("Wireless Charger Pad", "Electronics", 19.99, 500),
        ("Blender High-Speed", "Home & Kitchen", 99.99, 70)
    ]
    products = []
    for i, (name, category, price, stock) in enumerate(product_catalog, 1):
        cursor.execute(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            (name, category, price, stock)
        )
        products.append((i, price))

    # 2.3 Seed Employees (8 employees)
    departments = ["Sales", "Account Management", "Support"]
    employee_names = [
        ("John", "Doe", "Sales", 60000.00, "2023-01-15"),
        ("Jane", "Smith", "Sales", 62000.00, "2023-03-10"),
        ("Robert", "Johnson", "Account Management", 55000.00, "2023-06-01"),
        ("Emily", "Davis", "Support", 48000.00, "2024-01-10"),
        ("William", "Miller", "Sales", 61000.00, "2023-08-20"),
        ("Jessica", "Wilson", "Sales", 63000.00, "2023-11-05"),
        ("David", "Taylor", "Support", 47000.00, "2024-02-15"),
        ("Sarah", "Thomas", "Account Management", 56000.00, "2023-12-01")
    ]
    employees = []
    for i, (first, last, dept, salary, hire_date) in enumerate(employee_names, 1):
        cursor.execute(
            "INSERT INTO employees (first_name, last_name, department, salary, hire_date) VALUES (?, ?, ?, ?, ?)",
            (first, last, dept, salary, hire_date)
        )
        employees.append(i)

    # 2.4 Seed Orders and Sales (50+ orders, spanning 30 days)
    statuses = ["Completed", "Completed", "Completed", "Pending", "Cancelled"]
    current_time = datetime.utcnow()
    for order_id in range(1, 60):
        cust_id = random.choice(customers)
        emp_id = random.choice(employees)
        days_ago = random.randint(1, 30)
        order_date = (current_time - timedelta(days=days_ago, hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choice(statuses)

        # Decide items in this order (1 to 4 items)
        num_items = random.randint(1, 4)
        selected_prod_ids = random.sample(range(1, len(product_catalog) + 1), num_items)
        
        order_total = 0.00
        sales_records = []

        for p_id in selected_prod_ids:
            qty = random.randint(1, 3)
            unit_price = products[p_id - 1][1]
            discount = random.choice([0.00, 0.00, 0.00, 0.05, 0.10])
            item_total = float(qty) * float(unit_price) * (1.0 - discount)
            order_total += item_total
            sales_records.append((p_id, qty, unit_price, discount))

        # Insert Order
        cursor.execute(
            "INSERT INTO orders (customer_id, employee_id, order_date, status, total_amount) VALUES (?, ?, ?, ?, ?)",
            (cust_id, emp_id, order_date, status, round(order_total, 2))
        )
        
        # Insert Sales Items
        for p_id, qty, unit_price, discount in sales_records:
            cursor.execute(
                "INSERT INTO sales (order_id, product_id, quantity, unit_price, discount) VALUES (?, ?, ?, ?, ?)",
                (order_id, p_id, qty, unit_price, discount)
            )

    conn.commit()
    conn.close()

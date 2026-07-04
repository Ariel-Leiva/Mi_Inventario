import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from functools import wraps

def login_required(f):
    """Require user login for specific routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Configure application
app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
db = SQL("sqlite:///inventory.db")

@app.after_request
def after_request(response):
    """Disable response caching."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")

    # Get time filter (default: 'all')
    time_filter = request.args.get("time", "all")

    # Set SQL date condition
    date_condition = ""
    if time_filter == "today":
        date_condition = "AND date(s.sale_date) = date('now')"
    elif time_filter == "week":
        date_condition = "AND s.sale_date >= date('now', '-7 days')"
    elif time_filter == "month":
        date_condition = "AND s.sale_date >= date('now', '-30 days')"

    # Calculate revenue and profit
    totals = db.execute(f"""
        SELECT SUM(s.total_price) as revenue, SUM(s.profit) as profit
        FROM sales s
        WHERE s.user_id = ? {date_condition}
    """, session["user_id"])

    revenue = totals[0]["revenue"] or 0
    profit = totals[0]["profit"] or 0

    # Get top 5 selling products
    top_products = db.execute(f"""
        SELECT p.name, SUM(s.quantity) as total_sold
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE s.user_id = ? {date_condition}
        GROUP BY s.product_id
        ORDER BY total_sold DESC
        LIMIT 5
    """, session["user_id"])

    labels = [row["name"] for row in top_products]
    data = [row["total_sold"] for row in top_products]

    # Query low stock products
    low_stock_items = db.execute("""
        SELECT name, stock, min_stock
        FROM products
        WHERE user_id = ? AND stock <= min_stock
        ORDER BY stock ASC
    """, session["user_id"])

    # Render dashboard
    return render_template("index.html",
                           revenue=revenue,
                           profit=profit,
                           labels=labels,
                           data=data,
                           time_filter=time_filter,
                           low_stock_items=low_stock_items)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""

    # Handle form submission
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate inputs
        if not username or not password:
            flash("Debes ingresar un nombre de usuario y una contraseña.")
            return render_template("register.html")
        elif password != confirmation:
            flash("Las contraseñas no coinciden.")
            return render_template("register.html")

        # Save user to database
        try:
            # Hash password
            hash_pw = generate_password_hash(password)

            # Insert user
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_pw)

            flash("¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.")
            return redirect("/")

        except ValueError:
            # Handle duplicate username
            flash("El nombre de usuario ya está en uso. Elige otro.")
            return render_template("register.html")

    # Render registration page
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in user."""

    # Clear previous session
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Debes ingresar tu usuario y contraseña.")
            return render_template("login.html")

        # Query database for user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Verify credentials
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Nombre de usuario o contraseña inválidos.")
            return render_template("login.html")

        # Save user session
        session["user_id"] = rows[0]["id"]

        flash("¡Has iniciado sesión correctamente!")
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log out user."""
    # Clear session
    session.clear()
    return redirect("/")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add new product."""

    if request.method == "POST":
        name = request.form.get("name")
        buy_price = request.form.get("buy_price")
        sell_price = request.form.get("sell_price")
        stock = request.form.get("stock")
        min_stock = request.form.get("min_stock")

        # Validate inputs
        if not name or not buy_price or not sell_price or not stock:
            flash("Debes completar todos los campos obligatorios.")
            return render_template("add.html")

        # Check for duplicate product name
        existing_product = db.execute("SELECT * FROM products WHERE user_id = ? AND LOWER(name) = LOWER(?)", session["user_id"], name)

        if len(existing_product) > 0:
            flash(f"Ya tienes un producto llamado '{name}'. Si quieres agregar más unidades, usa el botón Editar.")
            return render_template("add.html")

        # Insert new product
        try:
            db.execute("""
                INSERT INTO products (user_id, name, buy_price, sell_price, stock, min_stock)
                VALUES (?, ?, ?, ?, ?, ?)
            """, session["user_id"], name, float(buy_price), float(sell_price), int(stock), int(min_stock))

            flash(f"¡Producto '{name}' agregado exitosamente!")
            return redirect("/")

        except ValueError:
            flash("Error al guardar el producto. Verifica los datos ingresados.")
            return render_template("add.html")

    else:
        # Render add product form
        return render_template("add.html")

@app.route("/products")
@login_required
def products():
    """Display user inventory."""

    # Query all user products
    inventory = db.execute("SELECT * FROM products WHERE user_id = ? ORDER BY name ASC", session["user_id"])

    # Calculate total items
    total_items = sum(item["stock"] for item in inventory)

    # Calculate total investment
    total_investment = sum(item["buy_price"] * item["stock"] for item in inventory)

    return render_template("products.html", inventory=inventory, total_items=total_items, total_investment=total_investment)

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Register product sale."""

    if request.method == "POST":
        product_id = request.form.get("product_id")
        quantity = request.form.get("quantity")

        # Validate inputs
        if not product_id or not quantity:
            flash("Debes seleccionar un producto y una cantidad.")
            return redirect("/sell")

        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash("La cantidad de venta debe ser mayor a cero.")
                return redirect("/sell")
        except ValueError:
            flash("Cantidad inválida.")
            return redirect("/sell")

        # Query product data
        product_data = db.execute("SELECT * FROM products WHERE id = ? AND user_id = ?", product_id, session["user_id"])

        if len(product_data) != 1:
            flash("Producto no encontrado.")
            return redirect("/sell")

        product = product_data[0]

        # Check stock availability
        if product["stock"] < quantity:
            flash(f"Stock insuficiente. Solo te quedan {product['stock']} unidades de '{product['name']}'.")
            return redirect("/sell")

        # Calculate total price and profit
        total_price = product["sell_price"] * quantity
        profit = (product["sell_price"] - product["buy_price"]) * quantity

        # Process transaction
        # Deduct stock
        db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", quantity, product_id)

        # Record sale
        db.execute("""
            INSERT INTO sales (user_id, product_id, quantity, total_price, profit)
            VALUES (?, ?, ?, ?, ?)
        """, session["user_id"], product_id, quantity, total_price, profit)

        flash(f"¡Venta exitosa! Vendiste {quantity}x {product['name']} por un total de ${total_price:.2f}.")
        return redirect("/products")

    else:
        # Render sell form with available products
        products = db.execute("SELECT id, name, stock, sell_price FROM products WHERE user_id = ? AND stock > 0 ORDER BY name ASC", session["user_id"])
        return render_template("sell.html", products=products)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    """Edit or delete product."""

    # Verify product ownership
    product_data = db.execute("SELECT * FROM products WHERE id = ? AND user_id = ?", id, session["user_id"])
    if len(product_data) != 1:
        flash("Producto no encontrado o no tienes permiso para editarlo.")
        return redirect("/products")

    product = product_data[0]

    if request.method == "POST":
        # Handle delete action
        if request.form.get("action") == "delete":

            # Check for existing sales
            sales_history = db.execute("SELECT * FROM sales WHERE product_id = ?", id)

            if len(sales_history) > 0:
                # Block deletion if sales exist
                flash("No puedes eliminar este producto porque ya tiene ventas registradas. Te recomendamos dejar su stock en 0.")
                return redirect(f"/edit/{id}")
            else:
                # Delete product
                db.execute("DELETE FROM products WHERE id = ?", id)
                flash(f"Producto '{product['name']}' eliminado correctamente.")
                return redirect("/products")

        # Handle update action
        name = request.form.get("name")
        buy_price = request.form.get("buy_price")
        sell_price = request.form.get("sell_price")
        stock = request.form.get("stock")
        min_stock = request.form.get("min_stock")

        # Check for name collision with other products
        existing_name = db.execute("""
            SELECT * FROM products
            WHERE user_id = ? AND LOWER(name) = LOWER(?) AND id != ?
        """, session["user_id"], name, id)

        if len(existing_name) > 0:
            flash(f"Ya tienes OTRO producto llamado '{name}'. Usa un nombre distinto.")
            return redirect(f"/edit/{id}")

        # Update product details
        db.execute("""
            UPDATE products
            SET name = ?, buy_price = ?, sell_price = ?, stock = ?, min_stock = ?
            WHERE id = ?
        """, name, float(buy_price), float(sell_price), int(stock), int(min_stock), id)

        flash(f"¡Producto '{name}' actualizado exitosamente!")
        return redirect("/products")

    else:
        # Render edit form
        return render_template("edit.html", product=product)

@app.route("/history")
@login_required
def history():
    """Display sales history."""

    # Query sales history
    sales_history = db.execute("""
        SELECT s.id, p.name, s.quantity, s.total_price, s.profit, s.sale_date
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE s.user_id = ?
        ORDER BY s.sale_date DESC
    """, session["user_id"])

    return render_template("history.html", history=sales_history)

if __name__ == "__main__":
    app.run(debug=True)

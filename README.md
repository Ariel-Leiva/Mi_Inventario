# MI INVENTARIO - PYME MANAGEMENT SYSTEM
#### Video Demo:  https://youtu.be/evQ2kqxmmqw
#### Description:

"Mi Inventario" (My Inventory) is a comprehensive, full-stack web application meticulously engineered to provide small and medium-sized enterprises (PyMEs) with an accessible, robust, and intuitive inventory and sales management solution. Born from the intersection of software engineering and business innovation, this platform bridges the critical gap between rudimentary, error-prone spreadsheet tracking and overly complex, prohibitively expensive enterprise resource planning (ERP) systems.

By centralizing product cataloging, stock monitoring, and financial analytics into a single responsive interface, the application empowers local business owners to make data-driven decisions and streamline their daily operations efficiently.

## Project Architecture and Tech Stack

The application is built upon a standard Model-View-Controller (MVC) architectural pattern, ensuring a clean separation of concerns and maintainable code.

* **Backend:** Python 3 powered by the Flask web framework.
* **Database:** SQLite3, utilizing the CS50 SQL library for streamlined database connections and query execution.
* **Frontend:** HTML5, CSS3, and JavaScript, enhanced by the Bootstrap 5 framework for responsive design and Chart.js for dynamic data visualization.
* **Authentication:** Session-based authentication using `Flask-Session` (filesystem) and password hashing via `Werkzeug.security`.

## Database Design

The relational database (`inventory.db`) is structured to ensure data integrity, prevent anomalies, and facilitate complex financial reporting. It consists of three primary tables:

1.  **`users` Table:** Handles secure access. It stores unique usernames and their corresponding bcrypt-hashed passwords.
2.  **`products` Table:** Acts as the central catalog. It stores the `name`, `buy_price` (cost), `sell_price` (retail), current `stock`, and a `min_stock` threshold for automated low-inventory alerts. It includes a Foreign Key referencing the user, ensuring isolated multi-tenancy (each user only sees their own data).
3.  **`sales` Table:** Functions as an immutable accounting ledger. Every transaction records the `product_id`, `quantity`, `total_price`, calculated `profit`, and a `DATETIME` timestamp.

To optimize performance, especially for the financial dashboard that aggregates massive amounts of data, explicit indices (`idx_products_user`, `idx_sales_user`, `idx_sales_product`) were implemented on the foreign keys, significantly reducing the algorithmic time complexity of read operations.

## Core Features and Engineering Decisions (Trade-offs)

During the development lifecycle, several critical design decisions and trade-offs were made to prioritize data integrity and user experience:

### 1. Data Integrity and Ledger Protection
One of the most crucial engineering decisions was handling product deletion. Initially, allowing a user to delete a product seemed standard. However, doing so would trigger a "Foreign Key Constraint" error if that product had existing records in the `sales` table, or worse, it would permanently corrupt the user's historical financial metrics if the sales were cascade-deleted.
**Trade-off:** I implemented a validation layer in the `/edit` route. If a product has an existing sales history, the system explicitly blocks its deletion. Instead, the user is advised to update the stock to zero. This ensures the immutable nature of the financial ledger, meaning the Revenue and Profit calculations on the dashboard will always remain 100% accurate.

### 2. Case-Insensitive Duplicate Prevention
To prevent database clutter and user error, the system includes a strict validation mechanism when adding or editing products. The application executes a SQL query using the `LOWER()` function to compare the requested product name against the existing database.
**Trade-off:** While this adds a slight overhead to the `INSERT` and `UPDATE` operations, it successfully prevents a user from accidentally creating redundant distinct SKUs for "Perfume", "perfume", and "PERFUME", which would otherwise fragment their stock tracking.

### 3. Client-Side DOM Manipulation vs. Server-Side Searching
The "My Products" view features a real-time search bar.
**Trade-off:** Instead of sending an asynchronous HTTP request (AJAX/Fetch) to the Flask backend on every keystroke (`keyup` event) to query the database—which would consume significant server bandwidth and introduce latency—I opted to handle the filtering entirely on the client-side using Vanilla JavaScript. The script iterates through the table rows in the DOM and toggles their CSS `display` property based on string matching. This offloads computation to the client's browser, resulting in a zero-latency, instantaneous search experience.

### 4. Responsive Data Visualization
Integrating Chart.js for the "Top 5 Selling Products" dashboard presented a challenge on mobile devices. By default, the library maintains a strict aspect ratio, which caused the chart to compress vertically on narrow smartphone screens, rendering the bar labels illegible.
**Trade-off:** I disabled the `maintainAspectRatio` property in the JavaScript configuration and wrapped the canvas in a responsive container with a fixed minimum height (`300px`). This ensures the UI remains highly readable and professional on both desktop monitors and mobile browsers.

## File Directory Overview

* **`app.py`:** The main application controller. It handles all routing, session validation, input sanitization, and complex SQL data aggregation (using `JOIN`, `SUM`, and `GROUP BY` clauses).
* **`schema.sql`:** The initialization script documenting the exact SQL schema, table relationships, and indexing strategies used to build `inventory.db`.
* **`templates/layout.html`:** The master Jinja2 template. It standardizes the UI with a modern, minimalist Bootstrap navigation bar, global font imports (Inter), and dynamic Flash message rendering.
* **`templates/index.html`:** The dynamic dashboard. It uses conditional rendering to display a marketing landing page for unauthenticated users, or a comprehensive financial overview with Chart.js for logged-in users.
* **`templates/sell.html` & `add.html` & `edit.html`:** The CRUD interface forms, fully secured with `required` HTML5 attributes and numeric step constraints.
* **`templates/history.html` & `products.html`:** Data presentation layers utilizing responsive tables and custom Jinja2 string formatting to display monetary values clearly (omitting decimals and using standard thousands separators).

## Conclusion
"Mi Inventario" successfully demonstrates the practical application of full-stack development principles, secure database design, and user-centric problem solving. It provides a highly functional, secure, and visually polished tool ready to deploy for real-world business management.

## Acknowledgements
During the development of this project, AI assistants (Gemini) were used as supplementary tools for debugging code, refactoring comments into professional English, and optimizing CSS/Bootstrap layouts, in accordance with the CS50 final project AI policy. The core logic, database architecture, and business requirements are my own original work.

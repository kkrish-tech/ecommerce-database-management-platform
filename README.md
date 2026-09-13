# 🛍️ Multi-Role E-Commerce Relational Database Platform

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

---

### 💡 Core Problem & Approach

Managing a multi-vendor marketplace requires strict data integrity, segregated role authorization, real-time inventory adjustments, and dynamic financial reporting. This project addresses operational complexity by building a relational database schema coupled with a Flask web microservice. It enforces granular Role-Based Access Control (RBAC) across three dedicated user portals while executing transactional SQL queries to guarantee inventory accuracy and generate system-wide business intelligence dashboards.

HTTP Request ──> Flask Router ──> RBAC Verification ──> MySQL Connector ──> Transaction / Report Query ──> Jinja2 / UI Render

---

### 📌 Project Overview
This project builds a full-stack relational database application designed for dynamic e-commerce operations. It features customized interface views and workflow controls for three distinct roles: **System Managers (Admins)**, **Vendors**, and **Customers**. The application streamlines product cataloging, transactional shopping carts, stock restoration upon order cancellation, review submissions, and aggregate statistical reporting.

---

### 🛠️ Technologies Used

* **Backend & API:** Python, Flask, `mysql-connector-python`, Python-dotenv
* **Database Management:** MySQL, Relational Schemas, SQL Aggregate Functions
* **Frontend & UI:** HTML5, CSS3, JavaScript (DOM Manipulation, Modal Management), Bootstrap 5

---

### 📌 Key Features

* **Role-Based Access Control (RBAC):** Authenticates System Managers, Vendors, and Customers with tailored route access and role-specific dashboards.
* **Real-Time Inventory & Order Transactions:** Automates stock deductions when customers purchase items and restores stock levels if pending orders are cancelled.
* **Integrated Business Intelligence Reports:** Calculates real-time system metrics including catalog stats, status-wise sales totals, vendor stock levels, category price bounds, and aggregate review ratings.
* **Product Catalog Filtering & Search:** Allows customers to filter products dynamically by category or keyword search strings.
* **Review & Rating Workflow:** Restricts product reviews strictly to verified customers who have ordered non-cancelled items.

---

### ⚙️ The Architecture & Portals

1. **System Manager (Admin) Portal**
   * Manages system-wide master records across Categories, Vendors, Customers, Products, Orders, and Reviews.
   * Oversees customer and vendor account statuses (Active, Inactive, Disabled) and assigns management contacts.
   * Monitors aggregate financial performance, revenue distributions, and high-level KPI cards on the main dashboard.

2. **Vendor Portal**
   * Allows vendors to log in and manage their own product catalogs, pricing, stock levels, and category assignments.
   * Tracks customer orders containing their specific inventory items.
   * Reviews product ratings and feedback submitted specifically for their inventory items.

3. **Customer Portal**
   * Enables user registration, login, and secure password update capabilities.
   * Provides catalog search and filtering tools paired with interactive order modals to purchase products.
   * Tracks order histories, enables order cancellation for items in `Processing` status, and submits product ratings/reviews.

---

### 📚 What I Learned
* **Transactional Integrity:** Implemented atomic SQL updates to ensure product stock quantities remain synchronized during concurrent customer purchases and order cancellations.
* **Relational Schema Design:** Structured foreign key constraints across `PRODUCT`, `CATEGORY`, `PRODUCT_CATEGORY`, `ORDER`, `ORDER_DETAILS`, `VENDOR`, `CUSTOMER`, and `REVIEW` tables to prevent orphan records.
* **Analytical SQL Aggregations:** Leveraged multi-table `JOIN` statements along with `GROUP BY` clauses, `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX` to compute live reporting summaries.

---

### 🚀 How Can It Be Improved?

* **Database Migration & ORM:** Transition raw `mysql-connector` SQL execution to an ORM framework like **SQLAlchemy** with **Alembic** migrations.
* **Authentication Security:** Upgrade plain-text password handling to secure password hashing using **Werkzeug** or **Bcrypt**.
* **Payment Gateway Integration:** Incorporate third-party checkout APIs like **Stripe** or **PayPal** for live transaction processing.
* **Containerization:** Package the Flask app and MySQL server into multi-container environments using **Docker** and **Docker Compose**.

---

## ▶️ Running the Project

### 1. Clone the repository

git clone [https://github.com/your-username/ecommerce-db-system.git](https://github.com/your-username/ecommerce-db-system.git)
cd ecommerce-db-system

### 2. Install dependencies

pip install flask mysql-connector-python python-dotenv

### 3. Environment Configuration

Create a .env file in the root directory and add your MySQL database connection credentials:

DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_database_name

### 4. Database Setup

Import your SQL schema and starter seed data into your MySQL instance:

mysql -u your_db_user -p your_database_name < schema.sql

### 5. Run the application

python user_interface.py

Open your browser and navigate to http://127.0.0.1:5000 to access the application dashboard.



# E-Commerce Database Management App
# Karthikeyan Kumaravel Krishnan

import os
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Loads MySQL login credentials from the .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ecommerce-db-system-key'

# Database Configuration using environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Makes and returns a connection to the MySQL database
def database_connect():
    try:
        connection = mysql.connector.connect(**db_config)
        print("Successfully connected to the MySQL database!")
        return connection
    except mysql.connector.Error as err:
        print(f"Error: Failed to connect to MySQL database: {err}")
        raise err


# ==============================================================================
# AUTHENTICATION PAGES
# ==============================================================================

# Home / Dashboard Page
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    # --- REPORT 1: High-Level Inventory KPIs ---
    cursor.execute("SELECT COUNT(*) AS total_products FROM PRODUCT")
    product_count = cursor.fetchone()['total_products'] or 0
    
    cursor.execute("SELECT SUM(StockQuantity) AS total_stock FROM PRODUCT")
    total_stock = cursor.fetchone()['total_stock'] or 0
    
    cursor.execute("SELECT AVG(Price) AS avg_price, MIN(Price) AS min_price, MAX(Price) AS max_price FROM PRODUCT")
    kpi_stats = cursor.fetchone()
    avg_price = round(float(kpi_stats['avg_price'] or 0.00), 2)
    min_price = round(float(kpi_stats['min_price'] or 0.00), 2)
    max_price = round(float(kpi_stats['max_price'] or 0.00), 2)
    
    # --- REPORT 2: Sales Summary ---
    cursor.execute("""
        SELECT OrderStatus, 
               COUNT(OrderID) AS OrderCount, 
               AVG(TotalOrderPrice) AS AvgOrderValue, 
               SUM(TotalOrderPrice) AS TotalRevenue
        FROM `ORDER`
        GROUP BY OrderStatus
    """)
    sales_summary = cursor.fetchall()
    
    # --- REPORT 3: Vendor Inventory Breakdown ---
    cursor.execute("""
        SELECT v.VendorName, 
               COUNT(p.ProductID) AS TotalProducts, 
               COALESCE(SUM(p.StockQuantity), 0) AS TotalStock
        FROM VENDOR v
        LEFT JOIN PRODUCT p ON v.VendorID = p.VendorID
        GROUP BY v.VendorID, v.VendorName
    """)
    vendor_summary = cursor.fetchall()
    
    # --- REPORT 4: Category Pricing Metrics ---
    cursor.execute("""
        SELECT c.CategoryName, 
               MIN(p.Price) AS MinPrice, 
               AVG(p.Price) AS AvgPrice, 
               MAX(p.Price) AS MaxPrice
        FROM CATEGORY c
        LEFT JOIN PRODUCT_CATEGORY pc ON c.CategoryID = pc.CategoryID
        LEFT JOIN PRODUCT p ON pc.ProductID = p.ProductID
        GROUP BY c.CategoryID, c.CategoryName
    """)
    category_summary = cursor.fetchall()
    
    # --- REPORT 5: Customer Reviews Summary ---
    cursor.execute("""
        SELECT p.ProductName, 
               COUNT(r.ReviewID) AS TotalReviews, 
               AVG(r.RatingStar) AS AvgRating
        FROM PRODUCT p
        JOIN REVIEW r ON p.ProductID = r.ProductID
        GROUP BY p.ProductID, p.ProductName
    """)
    review_summary = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template(
        'index.html', 
        product_count=product_count, 
        total_stock=total_stock, 
        avg_price=avg_price,
        min_price=min_price,
        max_price=max_price,
        sales_summary=sales_summary,
        vendor_summary=vendor_summary,
        category_summary=category_summary,
        review_summary=review_summary
    )

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # 'admin', 'customer', or 'vendor'
        
        connection = database_connect()
        cursor = connection.cursor(dictionary=True)
        
        # --- ADMIN LOGIN ---
        if role == 'admin':
            cursor.execute("SELECT * FROM SYSTEM_MANAGER WHERE Email = %s", (email,))
            user = cursor.fetchone()

            if user and user['Password'] == password:
                session['user_id'] = user['ManagerID']
                session['user_name'] = user['Name']
                session['role'] = 'admin'
                cursor.close()
                connection.close()
                return redirect(url_for('index'))

        # --- CUSTOMER LOGIN ---
        elif role == 'customer':
            cursor.execute("SELECT * FROM CUSTOMER WHERE Email = %s", (email,))
            user = cursor.fetchone()

            if user and user['Password'] == password:
                status = user.get('CustomerStatus', 'Active')
                if status in ['Disabled', 'Inactive']:
                    manager_id = user.get('ManagerID')
                    manager_info = None

                    if manager_id:
                        cursor.execute("SELECT Name, Email FROM SYSTEM_MANAGER WHERE ManagerID = %s", (manager_id,))
                        manager_info = cursor.fetchone()

                    manager_name = manager_info['Name'] if manager_info else "System Administrator"
                    manager_email = manager_info['Email'] if manager_info else "support@ecommerce.com"

                    cursor.close()
                    connection.close()

                    # Lets user know if their customer account is disabled
                    flash(
                        f"Your account is currently {status.lower()}. "
                        f"Please contact your assigned manager, {manager_name} ({manager_email}), for assistance.",
                        'danger'
                    )
                    return render_template('auth/login.html')

                # Customer logs in
                session['user_id'] = user['CustomerID']
                session['user_name'] = user['CustomerName']
                session['role'] = 'customer'
                cursor.close()
                connection.close()
                return redirect(url_for('index'))

        # --- VENDOR LOGIN ---
        elif role == 'vendor':
            cursor.execute("SELECT * FROM VENDOR WHERE Email = %s", (email,))
            vendor = cursor.fetchone()

            if vendor and vendor['Password'] == password:
                status = vendor.get('VendorStatus', 'Active')
                if status in ['Disabled', 'Inactive']:
                    manager_id = vendor.get('ManagerID')
                    manager_info = None

                    if manager_id:
                        cursor.execute("SELECT Name, Email FROM SYSTEM_MANAGER WHERE ManagerID = %s", (manager_id,))
                        manager_info = cursor.fetchone()

                    manager_name = manager_info['Name'] if manager_info else "System Administrator"
                    manager_email = manager_info['Email'] if manager_info else "support@ecommerce.com"

                    cursor.close()
                    connection.close()

                    # Lets user know if their vendor account is disabled
                    flash(
                        f"Your vendor account is currently {status.lower()}. "
                        f"Please contact your assigned manager, {manager_name} ({manager_email}), for assistance.",
                        'danger'
                    )
                    return render_template('auth/login.html')

                # Vendor logs in
                session['user_id'] = vendor['VendorID']
                session['user_name'] = vendor['VendorName']
                session['role'] = 'vendor'
                cursor.close()
                connection.close()
                return redirect(url_for('index'))
                
        cursor.close()
        connection.close()
        flash('Invalid login credentials or role.', 'danger')
        
    return render_template('auth/login.html')

# Sign-Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['customer_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone_number']
        address = request.form['shipping_address']
        
        connection = database_connect()
        cursor = connection.cursor()

        # Creates the account
        try:
            query = """
                INSERT INTO CUSTOMER (CustomerName, Email, Password, PhoneNumber, ShippingAddress) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, email, password, phone, address))
            connection.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error creating account: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()
            
    return render_template('auth/signup.html')

# Logout Page
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Change Password Page
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        current_pwd = request.form['current_password']
        new_pwd = request.form['new_password']
        
        connection = database_connect()
        cursor = connection.cursor(dictionary=True)
        role = session.get('role')

        # Verifies old password before changing it to the new one
        if role == 'admin':
            cursor.execute("SELECT Password FROM SYSTEM_MANAGER WHERE ManagerID = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user and user['Password'] == current_pwd:
                cursor.execute("UPDATE SYSTEM_MANAGER SET Password = %s WHERE ManagerID = %s", (new_pwd, session['user_id']))
                connection.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Incorrect current password.', 'danger')

        elif role == 'customer':
            cursor.execute("SELECT Password FROM CUSTOMER WHERE CustomerID = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user and user['Password'] == current_pwd:
                cursor.execute("UPDATE CUSTOMER SET Password = %s WHERE CustomerID = %s", (new_pwd, session['user_id']))
                connection.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Incorrect current password.', 'danger')

        elif role == 'vendor':
            cursor.execute("SELECT Password FROM VENDOR WHERE VendorID = %s", (session['user_id'],))
            user = cursor.fetchone()
            if user and user['Password'] == current_pwd:
                cursor.execute("UPDATE VENDOR SET Password = %s WHERE VendorID = %s", (new_pwd, session['user_id']))
                connection.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Incorrect current password.', 'danger')
                
        cursor.close()
        connection.close()
        
    return render_template('auth/change_password.html')


# ==============================================================================
# SYSTEM MANAGER (ADMIN) PAGES
# ==============================================================================

# --- MANAGE CATEGORY ---

# Category Page
@app.route('/categories')
def manage_categories():
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM CATEGORY")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin/admin_categories.html', categories=categories)

# Dropdown that lets admins add more categories
@app.route('/add_category', methods=['POST'])
def add_category():
    category_name = request.form['category_name']
    
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO CATEGORY (CategoryName) VALUES (%s)", (category_name,))
    connection.commit()
    cursor.close()
    connection.close()
    
    return redirect(url_for('manage_categories'))

# Search filter for category
@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        new_name = request.form['category_name']
        cursor.execute("UPDATE CATEGORY SET CategoryName = %s WHERE CategoryID = %s", (new_name, category_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('manage_categories'))
        
    cursor.execute("SELECT * FROM CATEGORY WHERE CategoryID = %s", (category_id,))
    category = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('admin/admin_edit_category.html', category=category)

# Delete categories from the system
@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM CATEGORY WHERE CategoryID = %s", (category_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    return redirect(url_for('manage_categories'))

# --- MANAGE VENDOR ---

@app.route('/vendors')
def manage_vendors():
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM VENDOR")
    vendors = cursor.fetchall()
    
    cursor.execute("SELECT ManagerID, Name FROM SYSTEM_MANAGER")
    managers = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_vendors.html', vendors=vendors, managers=managers)

# Vendor creating account
@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    v_name = request.form['vendor_name']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone_number']
    status = request.form['vendor_status']
    mgr_id_raw = request.form.get('manager_id')
    mgr_id = int(mgr_id_raw) if mgr_id_raw else None
    
    connection = database_connect()
    cursor = connection.cursor()
    
    query = """
        INSERT INTO VENDOR (VendorName, Email, Password, PhoneNumber, VendorStatus, ManagerID) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (v_name, email, password, phone, status, mgr_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Vendor added successfully!', 'success')
    return redirect(url_for('manage_vendors'))

# Vendor editing their account
@app.route('/edit_vendor/<int:vendor_id>', methods=['GET', 'POST'])
def edit_vendor(vendor_id):
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        v_name = request.form['vendor_name']
        email = request.form['email']
        phone = request.form['phone_number']
        status = request.form['vendor_status']
        mgr_id_raw = request.form.get('manager_id')
        mgr_id = int(mgr_id_raw) if mgr_id_raw else None
        
        query = """
            UPDATE VENDOR 
            SET VendorName = %s, Email = %s, PhoneNumber = %s, VendorStatus = %s, ManagerID = %s 
            WHERE VendorID = %s
        """
        cursor.execute(query, (v_name, email, phone, status, mgr_id, vendor_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('manage_vendors'))
        
    cursor.execute("SELECT * FROM VENDOR WHERE VendorID = %s", (vendor_id,))
    vendor = cursor.fetchone()
    
    cursor.execute("SELECT ManagerID, Name FROM SYSTEM_MANAGER")
    managers = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_edit_vendor.html', vendor=vendor, managers=managers)

# Vendor deleting their account
@app.route('/delete_vendor/<int:vendor_id>', methods=['POST'])
def delete_vendor(vendor_id):
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM VENDOR WHERE VendorID = %s", (vendor_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('manage_vendors'))

# --- MANAGE CUSTOMER ---

# Admin can read, add, edit, and delete customers
@app.route('/customers')
def manage_customers():
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM CUSTOMER")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT ManagerID, Name FROM SYSTEM_MANAGER")
    managers = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_customers.html', customers=customers, managers=managers)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    name = request.form['customer_name']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone_number']
    status = request.form['customer_status']
    address = request.form['shipping_address']
    mgr_id = request.form.get('manager_id') or None
    
    connection = database_connect()
    cursor = connection.cursor()
    
    query = """
        INSERT INTO CUSTOMER (CustomerName, Email, Password, PhoneNumber, CustomerStatus, ShippingAddress, ManagerID) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, email, password, phone, status, address, mgr_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Customer added successfully!', 'success')
    return redirect(url_for('manage_customers'))

@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['customer_name']
        email = request.form['email']
        phone = request.form['phone_number']
        status = request.form['customer_status']
        address = request.form['shipping_address']
        mgr_id = request.form.get('manager_id') or None
        
        query = """
            UPDATE CUSTOMER 
            SET CustomerName = %s, Email = %s, PhoneNumber = %s, CustomerStatus = %s, ShippingAddress = %s, ManagerID = %s 
            WHERE CustomerID = %s
        """
        cursor.execute(query, (name, email, phone, status, address, mgr_id, customer_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('manage_customers'))
        
    cursor.execute("SELECT * FROM CUSTOMER WHERE CustomerID = %s", (customer_id,))
    customer = cursor.fetchone()
    
    cursor.execute("SELECT ManagerID, Name FROM SYSTEM_MANAGER")
    managers = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_edit_customer.html', customer=customer, managers=managers)

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM CUSTOMER WHERE CustomerID = %s", (customer_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('manage_customers'))

# --- MANAGE PRODUCT ---

# Admin can read, add, edit, and delete products
@app.route('/products')
def manage_products():
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PRODUCT")
    products = cursor.fetchall()
    
    cursor.execute("SELECT VendorID, VendorName FROM VENDOR")
    vendors = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_products.html', products=products, vendors=vendors)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['product_name']
    price = request.form['price']
    stock = request.form['stock_quantity']
    desc = request.form['description']
    origin = request.form['country_of_origin']
    vendor_id = request.form['vendor_id']
    
    connection = database_connect()
    cursor = connection.cursor()
    query = """
        INSERT INTO PRODUCT (ProductName, Price, StockQuantity, Description, CountryOfOrigin, VendorID) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, price, stock, desc, origin, vendor_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    return redirect(url_for('manage_products'))

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['product_name']
        price = request.form['price']
        stock = request.form['stock_quantity']
        desc = request.form['description']
        origin = request.form['country_of_origin']
        vendor_id = request.form['vendor_id']
        
        query = """
            UPDATE PRODUCT 
            SET ProductName = %s, Price = %s, StockQuantity = %s, Description = %s, CountryOfOrigin = %s, VendorID = %s 
            WHERE ProductID = %s
        """
        cursor.execute(query, (name, price, stock, desc, origin, vendor_id, product_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('manage_products'))
        
    cursor.execute("SELECT * FROM PRODUCT WHERE ProductID = %s", (product_id,))
    product = cursor.fetchone()
    
    cursor.execute("SELECT VendorID, VendorName FROM VENDOR")
    vendors = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_edit_product.html', product=product, vendors=vendors)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM PRODUCT WHERE ProductID = %s", (product_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('manage_products'))

# --- MANAGE ORDERS ---

# Admin can edit and delete orders
@app.route('/manager/orders')
def manager_orders():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT o.OrderID, o.OrderDate, o.TotalOrderPrice, o.OrderStatus, c.CustomerName, c.Email 
        FROM `ORDER` o
        JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
        ORDER BY o.OrderDate DESC
    """
    cursor.execute(query)
    orders = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_orders.html', orders=orders)

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        new_status = request.form['order_status']
        cursor.execute("UPDATE `ORDER` SET OrderStatus = %s WHERE OrderID = %s", (new_status, order_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Order status updated successfully!', 'success')
        return redirect(url_for('manager_orders'))
        
    cursor.execute("SELECT * FROM `ORDER` WHERE OrderID = %s", (order_id,))
    order = cursor.fetchone()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_edit_order.html', order=order)

@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM `ORDER` WHERE OrderID = %s", (order_id,))
    connection.commit()
    
    cursor.close()
    connection.close()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('manager_orders'))

# --- MANAGE REVIEWS ---

# Admin can edit and delete customer reviews
@app.route('/manager/reviews')
def manager_reviews():
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT r.ReviewID, c.CustomerName, p.ProductName, r.RatingStar, r.Comment, r.Date 
        FROM REVIEW r
        JOIN CUSTOMER c ON r.CustomerID = c.CustomerID
        JOIN PRODUCT p ON r.ProductID = p.ProductID
        ORDER BY r.Date DESC
    """
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('admin/admin_reviews.html', reviews=reviews)

@app.route('/manager/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
def edit_manager_review(review_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        
        update_query = "UPDATE REVIEW SET RatingStar = %s, Comment = %s WHERE ReviewID = %s"
        cursor.execute(update_query, (rating, comment, review_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Review updated successfully by manager!', 'success')
        return redirect(url_for('manager_reviews'))
        
    cursor.execute("SELECT * FROM REVIEW WHERE ReviewID = %s", (review_id,))
    review = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not review:
        flash('Review not found.', 'danger')
        return redirect(url_for('manager_reviews'))
        
    return render_template('admin/admin_edit_review.html', review=review)

@app.route('/manager/reviews/delete/<int:review_id>', methods=['POST'])
def delete_manager_review(review_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    connection = database_connect()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM REVIEW WHERE ReviewID = %s", (review_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Review deleted by manager.', 'success')
    return redirect(url_for('manager_reviews'))


# ==============================================================================
# VENDOR PAGES
# ==============================================================================

@app.route('/vendor/products')
def vendor_products():
    if 'user_id' not in session or session.get('role') != 'vendor':
        flash('Please log in as a vendor to view your products.', 'danger')
        return redirect(url_for('login'))
        
    vendor_id = session['user_id']
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT p.*, c.CategoryID, c.CategoryName 
        FROM PRODUCT p
        LEFT JOIN PRODUCT_CATEGORY pc ON p.ProductID = pc.ProductID
        LEFT JOIN CATEGORY c ON pc.CategoryID = c.CategoryID
        WHERE p.VendorID = %s
        ORDER BY p.ProductID DESC
    """
    cursor.execute(query, (vendor_id,))
    products = cursor.fetchall()

    cursor.execute("SELECT CategoryID, CategoryName FROM CATEGORY ORDER BY CategoryName ASC")
    categories = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('vendor/vendor_products.html', products=products, categories=categories)

@app.route('/vendor/orders')
def vendor_orders():
    if 'user_id' not in session or session.get('role') != 'vendor':
        flash('Please log in as a vendor to view orders.', 'danger')
        return redirect(url_for('login'))
        
    vendor_id = session['user_id']
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT o.OrderID, o.OrderDate, o.OrderStatus, c.CustomerName, 
               p.ProductName, od.Quantity, od.TotalProductPrice
        FROM ORDER_DETAILS od
        JOIN `ORDER` o ON od.OrderID = o.OrderID
        JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
        JOIN PRODUCT p ON od.ProductID = p.ProductID
        WHERE p.VendorID = %s
        ORDER BY o.OrderDate DESC
    """
    cursor.execute(query, (vendor_id,))
    vendor_orders_list = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('vendor/vendor_orders.html', orders=vendor_orders_list)

@app.route('/vendor/reviews')
def vendor_reviews():
    if 'user_id' not in session or session.get('role') != 'vendor':
        flash('Please log in as a vendor to view product reviews.', 'danger')
        return redirect(url_for('login'))
        
    vendor_id = session['user_id']
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT r.ReviewID, p.ProductName, c.CustomerName, 
               r.RatingStar, r.Comment, r.Date
        FROM REVIEW r
        JOIN PRODUCT p ON r.ProductID = p.ProductID
        JOIN CUSTOMER c ON r.CustomerID = c.CustomerID
        WHERE p.VendorID = %s
        ORDER BY r.Date DESC
    """
    cursor.execute(query, (vendor_id,))
    reviews_list = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return render_template('vendor/vendor_reviews.html', reviews=reviews_list)

@app.route('/vendor/products/add', methods=['POST'])
def vendor_add_product():
    if 'user_id' not in session or session.get('role') != 'vendor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    vendor_id = session['user_id']
    product_name = request.form['product_name']
    category_id = request.form.get('category_id')
    price = request.form['price']
    stock = request.form['stock_quantity']
    country = request.form.get('country_of_origin', '')
    description = request.form.get('description', '')

    connection = database_connect()
    cursor = connection.cursor()

    try:
        query_prod = """
            INSERT INTO PRODUCT (ProductName, Price, StockQuantity, CountryOfOrigin, Description, VendorID)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_prod, (product_name, price, stock, country, description, vendor_id))
        new_product_id = cursor.lastrowid

        if category_id:
            query_cat = "INSERT INTO PRODUCT_CATEGORY (ProductID, CategoryID) VALUES (%s, %s)"
            cursor.execute(query_cat, (new_product_id, category_id))

        connection.commit()
        flash('New product added successfully!', 'success')
    except mysql.connector.Error as err:
        connection.rollback()
        flash(f'Error adding product: {err}', 'danger')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('vendor_products'))

@app.route('/vendor/products/edit/<int:product_id>', methods=['POST'])
def vendor_edit_product(product_id):
    if 'user_id' not in session or session.get('role') != 'vendor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    vendor_id = session['user_id']
    product_name = request.form['product_name']
    category_id = request.form.get('category_id')
    price = request.form['price']
    stock = request.form['stock_quantity']
    country = request.form.get('country_of_origin', '')
    description = request.form.get('description', '')

    connection = database_connect()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE PRODUCT 
            SET ProductName = %s, Price = %s, StockQuantity = %s, 
                CountryOfOrigin = %s, Description = %s
            WHERE ProductID = %s AND VendorID = %s
        """
        cursor.execute(query, (product_name, price, stock, country, description, product_id, vendor_id))

        if cursor.rowcount > 0:
            cursor.execute("DELETE FROM PRODUCT_CATEGORY WHERE ProductID = %s", (product_id,))
            if category_id:
                cursor.execute(
                    "INSERT INTO PRODUCT_CATEGORY (ProductID, CategoryID) VALUES (%s, %s)", 
                    (product_id, category_id)
                )

            connection.commit()
            flash('Product details updated successfully!', 'success')
        else:
            flash('Product not found or access denied.', 'danger')

    except mysql.connector.Error as err:
        connection.rollback()
        flash(f'Error updating product: {err}', 'danger')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('vendor_products'))


# ==============================================================================
# CUSTOMER PAGES
# ==============================================================================

@app.route('/customer/products', methods=['GET', 'POST'])
def customer_products():
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Please log in as a customer to browse products.', 'danger')
        return redirect(url_for('login'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    # Handle POST (Buying / Placing an Order)
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity_to_buy = int(request.form['quantity'])
        customer_id = session['user_id']
        
        cursor.execute("SELECT ProductName, Price, StockQuantity FROM PRODUCT WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            flash('Product not found.', 'danger')
        elif quantity_to_buy > product['StockQuantity']:
            flash(f"Insufficient stock! Only {product['StockQuantity']} available.", 'danger')
        else:
            total_price = product['Price'] * quantity_to_buy
            
            order_query = """
                INSERT INTO `ORDER` (CustomerID, OrderDate, TotalOrderPrice, OrderStatus) 
                VALUES (%s, NOW(), %s, 'Processing')
            """
            cursor.execute(order_query, (customer_id, total_price))
            order_id = cursor.lastrowid
            
            details_query = """
                INSERT INTO ORDER_DETAILS (OrderID, ProductID, Quantity, TotalProductPrice)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(details_query, (order_id, product_id, quantity_to_buy, total_price))
            
            new_stock = product['StockQuantity'] - quantity_to_buy
            cursor.execute("UPDATE PRODUCT SET StockQuantity = %s WHERE ProductID = %s", (new_stock, product_id))
            connection.commit()
            
            flash(f"Order placed successfully! Total cost: ${total_price:.2f}", 'success')
            cursor.close()
            connection.close()
            return redirect(url_for('customer_orders'))

    # Handle GET (Filtering & Catalog View)
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category_id', '').strip()

    cursor.execute("SELECT CategoryID, CategoryName FROM CATEGORY ORDER BY CategoryName ASC")
    categories = cursor.fetchall()

    query = """
        SELECT p.ProductID, p.ProductName, p.Price, p.StockQuantity, p.Description, 
               v.VendorName, p.CountryOfOrigin AS Country, c.CategoryName
        FROM PRODUCT p
        LEFT JOIN VENDOR v ON p.VendorID = v.VendorID
        LEFT JOIN PRODUCT_CATEGORY pc ON p.ProductID = pc.ProductID
        LEFT JOIN CATEGORY c ON pc.CategoryID = c.CategoryID
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND p.ProductName LIKE %s"
        params.append(f"%{search_query}%")

    if selected_category:
        query += " AND pc.CategoryID = %s"
        params.append(selected_category)

    query += " ORDER BY p.ProductID DESC"

    cursor.execute(query, params)
    products = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template(
        'customer/customer_products.html', 
        products=products, 
        categories=categories, 
        search_query=search_query, 
        selected_category=selected_category
    )

@app.route('/my_orders')
def customer_orders():
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Please log in as a customer to view your orders.', 'danger')
        return redirect(url_for('login'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    customer_id = session['user_id']
    
    query = """
        SELECT o.OrderID, o.OrderDate, o.TotalOrderPrice, o.OrderStatus, 
               p.ProductName, p.Price AS UnitPrice, od.Quantity 
        FROM `ORDER` o
        JOIN ORDER_DETAILS od ON o.OrderID = od.OrderID
        JOIN PRODUCT p ON od.ProductID = p.ProductID
        WHERE o.CustomerID = %s
        ORDER BY o.OrderDate DESC
    """
    cursor.execute(query, (customer_id,))
    rows = cursor.fetchall()
    
    cursor.close()
    connection.close()

    grouped_orders = {}
    for row in rows:
        order_id = row['OrderID']
        if order_id not in grouped_orders:
            grouped_orders[order_id] = {
                'OrderID': row['OrderID'],
                'OrderDate': row['OrderDate'],
                'TotalOrderPrice': row['TotalOrderPrice'],
                'OrderStatus': row['OrderStatus'],
                'order_items': []
            }
            
        grouped_orders[order_id]['order_items'].append({
            'ProductName': row['ProductName'],
            'Quantity': row['Quantity'],
            'UnitPrice': row['UnitPrice']
        })

    orders_list = list(grouped_orders.values())
    return render_template('customer/customer_orders.html', orders=orders_list)

# Makes sure the stock is reset back to where it was before the user bought the stock
@app.route('/customer/orders/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM `ORDER` WHERE OrderID = %s AND CustomerID = %s", (order_id, session['user_id']))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found.', 'danger')
    elif order['OrderStatus'] != 'Processing':
        flash('Only orders with "Processing" status can be cancelled.', 'warning')
    else:
        cursor.execute("UPDATE `ORDER` SET OrderStatus = 'Cancelled' WHERE OrderID = %s", (order_id,))
        connection.commit()
        
        cursor.execute("SELECT ProductID, Quantity FROM ORDER_DETAILS WHERE OrderID = %s", (order_id,))
        order_items = cursor.fetchall()
        
        for item in order_items:
            prod_id = item['ProductID']
            qty = item['Quantity']
            
            cursor.execute("SELECT StockQuantity FROM PRODUCT WHERE ProductID = %s", (prod_id,))
            prod = cursor.fetchone()
            
            if prod:
                new_stock = prod['StockQuantity'] + qty
                cursor.execute("UPDATE PRODUCT SET StockQuantity = %s WHERE ProductID = %s", (new_stock, prod_id))
                connection.commit()
            
        flash('Order has been successfully cancelled and stock restored.', 'success')
        
    cursor.close()
    connection.close()
    return redirect(url_for('customer_orders'))

# Customers can write down their reviews of the products they purchased
@app.route('/customer/reviews', methods=['GET', 'POST'])
def customer_reviews():
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Please log in as a customer.', 'danger')
        return redirect(url_for('login'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    customer_id = session['user_id']
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        rating = int(request.form['rating'])
        comment = request.form['comment']
        
        check_purchase_query = """
            SELECT 1 FROM `ORDER` o
            JOIN ORDER_DETAILS od ON o.OrderID = od.OrderID
            WHERE o.CustomerID = %s AND od.ProductID = %s AND o.OrderStatus != 'Cancelled'
        """
        cursor.execute(check_purchase_query, (customer_id, product_id))
        has_purchased = cursor.fetchone()
        
        if not has_purchased:
            flash('You can only review products you have successfully ordered and purchased.', 'warning')
        else:
            insert_query = """
                INSERT INTO REVIEW (CustomerID, ProductID, RatingStar, Comment, Date)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_query, (customer_id, product_id, rating, comment))
            connection.commit()
            flash('Review submitted successfully!', 'success')
            
        cursor.close()
        connection.close()
        return redirect(url_for('customer_reviews'))
        
    purchased_products_query = """
        SELECT DISTINCT p.ProductID, p.ProductName 
        FROM `ORDER` o
        JOIN ORDER_DETAILS od ON o.OrderID = od.OrderID
        JOIN PRODUCT p ON od.ProductID = p.ProductID
        WHERE o.CustomerID = %s AND o.OrderStatus != 'Cancelled'
    """
    cursor.execute(purchased_products_query, (customer_id,))
    purchased_products = cursor.fetchall()
    
    reviews_query = """
        SELECT r.ReviewID, p.ProductName, r.RatingStar, r.Comment, r.Date 
        FROM REVIEW r
        JOIN PRODUCT p ON r.ProductID = p.ProductID
        WHERE r.CustomerID = %s
        ORDER BY r.Date DESC
    """
    cursor.execute(reviews_query, (customer_id,))
    my_reviews = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('customer/customer_reviews.html', purchased_products=purchased_products, my_reviews=my_reviews)

@app.route('/customer/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
def edit_customer_review(review_id):
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
        
    connection = database_connect()
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        
        update_query = """
            UPDATE REVIEW SET RatingStar = %s, Comment = %s 
            WHERE ReviewID = %s AND CustomerID = %s
        """
        cursor.execute(update_query, (rating, comment, review_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Review updated successfully!', 'success')
        return redirect(url_for('customer_reviews'))
        
    cursor.execute("SELECT * FROM REVIEW WHERE ReviewID = %s AND CustomerID = %s", (review_id, session['user_id']))
    review = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not review:
        flash('Review not found.', 'danger')
        return redirect(url_for('customer_reviews'))
        
    return render_template('customer/customer_edit_review.html', review=review)

@app.route('/customer/reviews/delete/<int:review_id>', methods=['POST'])
def delete_customer_review(review_id):
    if 'user_id' not in session or session.get('role') != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
        
    connection = database_connect()
    cursor = connection.cursor()
    
    cursor.execute("DELETE FROM REVIEW WHERE ReviewID = %s AND CustomerID = %s", (review_id, session['user_id']))
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Review deleted successfully.', 'success')
    return redirect(url_for('customer_reviews'))

# Main method
if __name__ == '__main__':
    app.run(debug=True)
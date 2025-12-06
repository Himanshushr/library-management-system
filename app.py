# app.py (FULL UPDATED CONTENT)

from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB_NAME = 'library.db'
user_counter = 103 # Maintain counter for new users

# --- Database Connection Utility ---

def get_db_connection():
    """Returns a database connection with row factory enabled for dictionary access."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- HTML Routes (Fetching data from DB for rendering) ---

@app.route('/')
@app.route('/login.html')
def login_page():
    return render_template('login.html') 

@app.route('/index.html')
def home():
    return render_template('index.html')

@app.route('/issue_return.html')
def issue_return_page():
    return render_template('issue_return.html')

@app.route('/fine_payment.html')
def fine_payment_page():
    return render_template('fine_payment.html')

@app.route('/membership.html')
def membership_page():
    conn = get_db_connection()
    users_db = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    users_dict = {row['user_id']: dict(row) for row in users_db}
    return render_template('membership.html', users=users_dict)

@app.route('/admin.html')
def admin_page():
    conn = get_db_connection()
    
    books = conn.execute("SELECT * FROM books").fetchall()
    users = conn.execute("SELECT * FROM users").fetchall()
    issues = conn.execute("SELECT * FROM transactions WHERE is_returned = 0").fetchall()
    
    conn.close()
    
    # Convert Row objects to dictionaries for template rendering
    books_list = [dict(row) for row in books]
    users_dict = {row['user_id']: dict(row) for row in users}
    issues_list = [dict(row) for row in issues]

    return render_template('admin.html', 
        books=books_list,
        users=users_dict,
        issues=issues_list
    )

# -------------------------------------------------------------
# --- API Endpoints: Issue/Return (Database Logic) ---
# -------------------------------------------------------------

@app.route('/api/search_book', methods=['POST'])
def search_book():
    data = request.get_json()
    query = data.get('query', '').lower()
    
    conn = get_db_connection()
    # Search by serial_no, title, or author
    sql_query = """
        SELECT serial_no, title, author, available_copies
        FROM books
        WHERE serial_no LIKE ? OR title LIKE ? OR author LIKE ?
    """
    results = conn.execute(sql_query, (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    return jsonify({"success": True, "results": [dict(row) for row in results]})

@app.route('/api/issue_book', methods=['POST'])
def issue_book():
    data = request.get_json()
    book_id = data.get('book_id')
    user_id = data.get('user_id')
    issue_date = data.get('issue_date')
    return_date = data.get('return_date')

    conn = get_db_connection()
    user = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"success": False, "message": "User not found or Membership invalid."}), 400
    
    book = conn.execute("SELECT available_copies, title FROM books WHERE serial_no = ?", (book_id,)).fetchone()
    
    if book and book['available_copies'] > 0:
        # 1. Insert new transaction
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (serial_no, user_id, issue_date, due_date)
            VALUES (?, ?, ?, ?)
        """, (book_id, user_id, issue_date, return_date))
        
        # 2. Decrement available copies
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE serial_no = ?", (book_id,)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Book '{book['title']}' successfully issued to {user_id}."})
    
    conn.close()
    return jsonify({"success": False, "message": "Book not available or not found."}), 400

@app.route('/api/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    serial_no = data.get('serial_no')
    actual_return_date_str = data.get('return_date')

    conn = get_db_connection()
    loan = conn.execute(
        "SELECT transaction_id, due_date, serial_no FROM transactions WHERE serial_no = ? AND is_returned = 0", 
        (serial_no,)
    ).fetchone()
    
    if not loan:
        conn.close()
        return jsonify({"success": False, "message": f"No active loan found for serial number {serial_no}."}), 404

    try:
        due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
        actual_return_date = datetime.strptime(actual_return_date_str, '%Y-%m-%d').date()
        
        fine_amount = 0.0
        if actual_return_date > due_date:
            days_late = (actual_return_date - due_date).days
            fine_amount = days_late * 5.0 # $5 fine per day late (MOCK)
            
        # Get book title for response message
        book = conn.execute("SELECT title FROM books WHERE serial_no = ?", (serial_no,)).fetchone()

        # NOTE: We update the transaction record with fine and return_date, 
        # but mark 'is_returned' only after fine confirmation.
        conn.execute(
            "UPDATE transactions SET fine_amount = ?, return_date = ? WHERE transaction_id = ?",
            (fine_amount, actual_return_date_str, loan['transaction_id'])
        )
        # Note: Availability update moved to confirm_fine to handle system crash scenario,
        # but kept in the mock for simplicity (assuming system is stable here).
        # We temporarily comment out the increase here to ensure it only happens at final confirmation.
        # conn.execute("UPDATE books SET available_copies = available_copies + 1 WHERE serial_no = ?", (serial_no,))
        
        conn.commit()
        conn.close()
            
        return jsonify({
            "success": True, 
            "message": "Return check successful.", 
            "fine_amount": fine_amount,
            "book_title": book['title'] if book else "Book",
            "transaction_id": loan['transaction_id'] # Use unique ID for payment lookup
        })

    except ValueError:
        conn.close()
        return jsonify({"success": False, "message": "Invalid date format."}), 400

# -------------------------------------------------------------
# --- API Endpoints: Fine Payment (Database Logic) ---
# -------------------------------------------------------------

@app.route('/api/confirm_fine', methods=['POST'])
def confirm_fine():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    fine_paid = float(data.get('fine_paid', 0))
    remarks = data.get('remarks')
    pending_fine = data.get('pending_fine')

    if not remarks:
        return jsonify({"success": False, "message": "Remarks field is mandatory."}), 400
    
    conn = get_db_connection()
    loan = conn.execute(
        "SELECT serial_no, fine_amount, is_returned FROM transactions WHERE transaction_id = ?", 
        (transaction_id,)
    ).fetchone()

    if not loan:
        conn.close()
        return jsonify({"success": False, "message": "Invalid transaction reference."}), 400
    
    if loan['is_returned'] == 1:
        conn.close()
        return jsonify({"success": False, "message": "Transaction already finalized."}), 400

    calculated_fine = loan['fine_amount']
    
    if calculated_fine > 0 and fine_paid < calculated_fine and not pending_fine:
        conn.close()
        return jsonify({"success": False, "message": "Full fine must be paid or Pending Fine must be checked to complete return."}), 400
        
    # Finalize the return: Mark as returned and increase book availability
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE transactions SET is_returned = 1 WHERE transaction_id = ?", 
        (transaction_id,)
    )
    cursor.execute(
        "UPDATE books SET available_copies = available_copies + 1 WHERE serial_no = ?",
        (loan['serial_no'],)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Transaction complete. Book returned successfully."})


# -------------------------------------------------------------
# --- API Endpoints: Membership Management (Database Logic) ---
# -------------------------------------------------------------

@app.route('/api/add_membership', methods=['POST'])
def add_membership():
    global user_counter
    data = request.get_json()
    name = data.get('name')
    membership_type = data.get('membership_type')

    if not all([name, membership_type]):
        return jsonify({"success": False, "message": "All fields are mandatory (Name, Membership Type)."}), 400

    duration = 365 if '1 year' in membership_type else 180
    new_user_id = f"U{user_counter}"
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO users (user_id, name, membership_type, expiry_date) VALUES (?, ?, ?, ?)",
        (new_user_id, name, membership_type, (datetime.now().date() + timedelta(days=duration)).isoformat())
    )
    conn.commit()
    conn.close()
    user_counter += 1
    
    return jsonify({"success": True, "message": f"Membership added successfully for {name}. User ID: {new_user_id}"})


@app.route('/api/update_membership', methods=['POST'])
def update_membership():
    data = request.get_json()
    user_id = data.get('user_id')
    extension = data.get('extension') 

    if not extension:
        return jsonify({"success": False, "message": "Extension period (6 months) must be selected."}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT expiry_date FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"success": False, "message": "User not found."}), 404
        
    extension_days = 180
    current_expiry = datetime.strptime(user['expiry_date'], '%Y-%m-%d').date()
    new_expiry = (current_expiry + timedelta(days=extension_days)).isoformat()
    
    conn.execute(
        "UPDATE users SET expiry_date = ? WHERE user_id = ?",
        (new_expiry, user_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Membership for {user_id} extended by 6 months. New expiry: {new_expiry}"})


@app.route('/api/manage_user', methods=['POST'])
def manage_user():
    data = request.get_json()
    user_id = data.get('user_id')
    action = data.get('action') 

    if not user_id:
        return jsonify({"success": False, "message": "User ID is mandatory."}), 400
    
    if action == 'new':
        return jsonify({"success": False, "message": "To add a new user, use the 'Add Membership' form."}), 400
    
    if action == 'existing':
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()

        if not user:
            return jsonify({"success": False, "message": f"User ID {user_id} not found."}), 404
        
        return jsonify({
            "success": True, 
            "message": f"User details fetched.",
            "user_details": dict(user)
        })
    
    return jsonify({"success": False, "message": "Invalid action selected."}), 400

# -------------------------------------------------------------
# --- API Endpoints: Admin Maintenance (Database Logic) ---
# -------------------------------------------------------------

@app.route('/api/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    serial_no = data.get('serial_no')
    available = int(data.get('available', 0))

    if not all([title, author, serial_no]):
        return jsonify({"success": False, "message": "All fields (Title, Author, Serial No.) are mandatory."}), 400

    conn = get_db_connection()
    existing = conn.execute("SELECT 1 FROM books WHERE serial_no = ?", (serial_no,)).fetchone()
    
    if existing:
        conn.close()
        return jsonify({"success": False, "message": f"Book with Serial No. {serial_no} already exists."}), 400

    conn.execute(
        "INSERT INTO books (serial_no, title, author, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
        (serial_no, title, author, available, available)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Book '{title}' (SN: {serial_no}) added successfully."})


if __name__ == '__main__':
    # It is recommended to run database_setup.py first.
    print("Running Flask app (connected to library.db). Access the login page at http://127.0.0.1:5000/")
    app.run(debug=True)
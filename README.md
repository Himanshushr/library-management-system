📚 Library Management System
Project Description
This is a Library Management System built using Python Flask and SQLite, managing core library transactions. It features modules for Issue/Return, Fine Payment, Membership creation, and an Admin Dashboard for reporting and maintenance.

Shutterstock
Explore

The system uses a centralized database for persistent storage of books, users, and loan records.

🚀 Key Features
Authentication: Basic login functionality (Admin/User).

Inventory Management: Add new books (Admin) and check real-time availability.

Transaction Management: Issue books to members and process returns.

Financials: Automatic calculation of fines based on late returns and a dedicated Fine Payment module.

Membership: Forms to add new members and update/extend existing memberships.

Reporting: Admin view includes active loans, current inventory, and user lists.

💻 Technology Stack
Backend Framework: Python 3 + Flask

Database: SQLite3 (Stored in library.db)

Frontend: HTML5, CSS3, JavaScript (Client-side logic and API calls)

🛠️ Setup and Installation
Follow these steps to get the Library Management System up and running:

1. Prerequisites
You must have Python 3 installed on your system.

2. Install Dependencies
Open your terminal or command prompt and install Flask:

Bash

pip install Flask
3. Database Initialization
The project uses a separate file (database_setup.py) to create the SQLite file (library.db) and seed initial data (Admin user, Books, Members).

Run the setup file first:

Bash

python database_setup.py
This creates library.db and populates the books, users, and transactions tables.

4. Run the Application
Now, run the main Flask application:

Bash

python app.py
The application will start, and you can access it in your web browser at:

http://127.0.0.1:5000/
🔑 Credentials (Mock Login)
Use the following mock credentials to test the system:

Role	Username	Password	Access
Admin	admin	1234	All modules (Maintenance, Reporting, Transactions)
User	user	guest	Transaction modules (Issue/Return, Fine)

Export to Sheets

📂 Project Structure
This project assumes all files are placed in the same directory for simplicity, with the CSS/JS files referenced directly.

/library-system/
|-- app.py                  # Flask application & database API logic
|-- database_setup.py       # Script to create and seed library.db
|-- library.db              # SQLite database file (created upon setup)
|-- script.js               # Frontend JavaScript logic (API calls, UI updates)
|-- style.css               # Basic styling
|-- index.html              # Home/Navigation page
|-- login.html              # System entry point
|-- issue_return.html       # Issue and Return book transactions
|-- fine_payment.html       # Fine confirmation and payment
|-- membership.html         # User/Membership management
|-- admin.html              # Admin reports and book maintenance

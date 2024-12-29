# DigitalRisk Flask Project

Welcome to DigitalRisk! This Flask-based project is designed to provide OCR (Optical Character Recognition) capabilities for bank books, assisting bank officers in making loan decisions for customers. Below are the instructions to get started with running this project locally.

## Prerequisites

-  Python 3.10 installed on your local machine
-  `pip` package manager
-  MySQL database (or another compatible sql database)

## Beginner's Guide to Python and MySQL
- Install Python 3.10
Download Python 3.10 at the official Python website at python.org. Locate the downloaded file (e.g., python-3.10.0-amd64.exe) and download it, then install it.
In the installer window, check the box labeled "Add Python 3.10 to PATH." This ensures you can run Python from the command line.
- MySQL
Download MySQL at https://dev.mysql.com/downloads/installer/
Choose the "Developer Default" (Full) setup type.
Follow the prompts to complete the installation, setting a root password when prompted. Do not lose this root password.

## Getting Started

1. **Clone the repository:**

   ```bash
   git clone https://github.com/rzputradev/digitalrisk.git
   cd digitalrisk
   ```

2. **Install dependencies:**

First, create a virtual environment (replace venv with env if you prefer):

```bash
python -m venv venv
```

Activate the virtual environment (Windows):

```bash
venv\Scripts\activate
```

Activate the virtual environment (MacOS/Linux):

```bash
source venv/bin/activate
```

Install all package

```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a .env file in the root of the project with the following configuration:

```plaintext
FLASK_ENV = development  # Set to 'development' or 'production'
SECRET_KEY = <your_secret_key>
DEV_DATABASE_URI = <your_dev_database_uri>
```

4. **Create the database:**

Before migrating, ensure you have created the development database. For example, using MySQL:

```bash
create database digitalrisk_db
```

**Database migration:**

DigitalRisk uses Flask-Migrate for database migrations. Run the following commands to set up your database schema:

```bash
flask db init  # Initialize migrations (first time only)
flask db migrate  # Create migration scripts
flask db upgrade  # Apply migrations to the database
```

Some of 

Run the application:

Do not forget to ensure you run the virtual environment

```bash
flask run.py 
```

Navigate to http://localhost:5000 in your web browser to view the application.

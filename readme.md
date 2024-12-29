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
Ensure do not have extension file other than .env. For example: .env in the explorer

```plaintext
FLASK_ENV = production  # Set to 'development' or 'production'
SECRET_KEY = <your_secret_key>
DEV_DATABASE_URI = <your_dev_database_uri> # comment either one of the dev or prod, depending on the environment you created
PROD_DATABASE_URI = <your_prod_database_uri> # comment either one of the dev or prod, depending on the environment you created
```


4. **Create the database:**

Before migrating, ensure you have created the development database. 
Run MySQL 8.0 Command Line or workbench, then fill-in the root password of the database
For example, using MySQL:

```bash
create database digitalrisk_db;
```

Then go back to regular command line / python
DigitalRisk uses Flask-Migrate for database migrations. Run the following commands in python or regular command line to set up your database schema:

```bash
flask db init  # Initialize migrations (first time only), if error, check the error message, probably install 'pymysql'
flask db migrate  # Create migration scripts
flask db upgrade  # Apply migrations to the database
```


5. **Fill-in the necessary data for the database:**

Some data need to be input to the database to ensure the proper creation of the database
Run MySQL 8.0 Command Line or workbench, then put the following query

**Database migration:**
``` SQL command line / workbench
USE digitalrisk_db;

INSERT INTO digitalrisk_db.application_type (name, description, created_at, updated_at)
VALUES
('Kredit Tanpa Agunan (KTA)', 'Pinjaman tanpa jaminan apa pun, biasanya ditawarkan oleh bank atau lembaga keuangan.', NOW(), NOW()),
('Kredit Usaha Rakyat (KUR)', 'Pinjaman bersubsidi pemerintah dengan bunga relatif rendah untuk pelaku UMKM.', NOW(), NOW()),
('Kredit Pemilikan Rumah (KPR)', 'Pinjaman jangka panjang untuk membeli atau memiliki rumah.', NOW(), NOW()),
('Kredit Kendaraan Bermotor (KKB)', 'Pinjaman untuk membeli kendaraan, biasanya mobil atau motor.', NOW(), NOW()),
('Kredit Multiguna', 'Pinjaman dengan jaminan aset tertentu yang dapat digunakan untuk berbagai kebutuhan.', NOW(), NOW()),
('Kredit Modal Kerja', 'Pinjaman khusus untuk tambahan modal usaha, dengan jangka waktu tertentu sesuai kebutuhan bisnis.', NOW(), NOW());
```

6. **Run the application:**

Do not forget to ensure you run the virtual environment (ensure you are in the right folder first)

```command line / bash
cd digitalrisk (if you are not in the folder)
venv\Scripts\activate
```

```bash
flask run.py (or try flask run)
```

Navigate to http://localhost:5000 in your web browser to view the application.

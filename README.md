# TCGApp – One Piece Card Identification and Price Tracker

TCGApp is a Django-based web application that allows users to upload images of One Piece trading cards, identify them using Google Cloud Vision OCR, and view pricing information from CSV data. This tool is designed for casual collectors and competitive players who want fast, accurate card identification and price tracking.

---

## 🚀 Features

- 🔍 Card image identification using OCR  
- 💰 CSV-based card pricing display (low/mid/high/market)  
- 🧑‍💼 User login and registration  
- 🗂️ Admin dashboard for managing uploaded images  
- 📁 Card database managed through Django ORM  
- 🔄 Custom command for importing cleaned data  
- 🛠️ Agile-based development workflow  

---

## 📦 Requirements

Ensure you have the following installed:

- Python 3.9 or later  
- pip (Python package manager)  
- Virtualenv (recommended)  
- Git (to clone the repository)  
- Google Cloud Vision API credentials  

---

## 🛠 Setup Instructions

1. **Clone the Repository**

    ```bash
    git clone https://github.com/jaredthecarrot/TCGApp.git
    cd TCGApp
    ```

2. **Create and Activate a Virtual Environment**

    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Django (latest) and Other Dependencies**

    ```bash
    pip install django
    pip install -r requirements.txt
    ```

---

## 🔐 Google Cloud Vision Setup

1. Create a Google Cloud project.  
2. Enable the **Cloud Vision API**.  
3. Generate a **Service Account Key** and download it as a `.json` file.  
4. Set the environment variable so the app can authenticate:

    ```bash
    # Windows
    set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\key.json

    # macOS/Linux
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/key.json
    ```

---

## 🧱 Database and Migrations

Run the following commands to apply migrations and initialize the database:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```


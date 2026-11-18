# Matcha Corner

Matcha Corner is a simple web application made using FastAPI, HTML, CSS, and SQLite. It allows users to register, log in, and add matcha products with their name, price, and variant. The added products are saved in the database and displayed on the main page.

## Development

I used the concepts and code logic from our previous activities with Sir Amiel, especially for the HTML forms and connecting them to the backend. I also combined and adjusted some parts to fit my matcha-themed project.

I used a little AI assistance for the more complicated parts, mainly organizing the structure of `app.py`, connecting the functions, and implementing password hashing.

## How to Run

1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `uvicorn app:app --reload`
3. Open `http://127.0.0.1:8000`

The application can also be tested using Postman through its API endpoints.

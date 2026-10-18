import sqlite3

DB_FILE = "prices.db"

def init_db():
    """Initializes the database and seeds ticket prices if empty."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                city TEXT PRIMARY KEY,
                price REAL
            )
        """)
        ticket_prices = {
            "london": 799.0,
            "paris": 899.0,
            "tokyo": 1420.0,
            "sydney": 2999.0,
            "berlin": 499.0,
            "new york": 950.0
        }
        for city, price in ticket_prices.items():
            cursor.execute("""
                INSERT INTO prices (city, price) VALUES (?, ?)
                ON CONFLICT(city) DO UPDATE SET price = ?
            """, (city.lower(), price, price))
        conn.commit()

def get_ticket_price(city: str) -> str:
    print(f"[TOOL] Querying database for city: {city}", flush=True)
    clean_city = city.strip().lower()  # یکسان‌سازی حروف کوچک
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price FROM prices WHERE lower(city) = ?", (clean_city,))
        result = cursor.fetchone()
        if result:
            return f"Ticket price to {clean_city.title()} is ${result[0]:.2f}"
        return f"No ticket price data available for {clean_city.title()}."
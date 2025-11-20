from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os
from typing import List, Optional

app = FastAPI(title="Expense Tracker API")

# --- Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
DEFAULT_CATEGORIES = ["Food", "Transportation", "Utilities", "Personal Care", "Entertainment", "Health", "Other"]

# --- Pydantic Models (Data Validation) ---
class ExpenseCreate(BaseModel):
    date: str
    amount: float
    category: str
    subcategory: Optional[str] = ""
    note: Optional[str] = ""

class ExpenseResponse(ExpenseCreate):
    id: int

class DateRange(BaseModel):
    start_date: str
    end_date: str

# --- Database Helper ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

# Initialize DB on startup
init_db()

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running"}

@app.get("/categories", response_model=List[str])
def get_categories():
    """Return a list of categories."""
    # In a real app, you might read this from a file or DB table
    return DEFAULT_CATEGORIES

@app.post("/expenses/", response_model=ExpenseResponse)
def add_expense(expense: ExpenseCreate):
    """Add a new expense."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (expense.date, expense.amount, expense.category, expense.subcategory, expense.note)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return {**expense.dict(), "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/", response_model=List[ExpenseResponse])
def list_expenses(start_date: str, end_date: str):
    """List expenses within a date range."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
            """,
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/summary/")
def get_summary(start_date: str, end_date: str):
    """Get total expenses grouped by category."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        return [{"category": row["category"], "total": row["total"]} for row in rows]

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"message": "Expense deleted successfully"}
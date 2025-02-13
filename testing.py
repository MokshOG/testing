import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Database setup
DB_NAME = "expenses.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                date TEXT,
                amount REAL,
                category TEXT,
                transaction_type TEXT
            )
        """)
        conn.commit()

init_db()

def add_expense(user, amount, category, transaction_type):
    current_date = datetime.now().strftime("%d/%m/%Y")
    if transaction_type == "Debit":
        amount = -abs(amount)
    else:
        amount = abs(amount)
    
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO expenses (user, date, amount, category, transaction_type) VALUES (?, ?, ?, ?, ?)",
                  (user, current_date, amount, category, transaction_type))
        conn.commit()

def read_expenses():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT user, date, amount, category, transaction_type FROM expenses")
        records = c.fetchall()
    return records

def filter_expenses_by_period(user, period):
    records = read_expenses()
    df = pd.DataFrame(records, columns=["User", "Date", "Amount", "Category", "Transaction Type"])
    df = df[df['User'] == user]
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    
    if period == "Monthly":
        df = df[df["Date"].dt.month == datetime.now().month]
    elif period == "Yearly":
        df = df[df["Date"].dt.year == datetime.now().year]
    return df.values.tolist()

def delete_expense(user, index):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE user=? AND id IN (SELECT id FROM expenses WHERE user=? LIMIT 1 OFFSET ?)",
                  (user, user, index))
        conn.commit()
        st.success("Expense deleted successfully!")

st.title("💰 Family Expense Tracker")

records = read_expenses()
users = list(set([record[0] for record in records]))
selected_user = st.selectbox("Select User:", ["New User"] + users)

if selected_user == "New User":
    new_user = st.text_input("Enter Your Name:").strip()
    if new_user:
        user = new_user
else:
    user = selected_user

menu = ["Add Expense", "View Summary"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Expense":
    st.subheader("Add a New Expense or Income")
    transaction_type = st.radio("Select Transaction Type:", ["Credit", "Debit"])
    amount = st.number_input("Enter Amount:", min_value=1, max_value=100000, value=1)
    category = st.text_input("Enter Category:")
    if st.button("Add Transaction"):
        add_expense(user, amount, category, transaction_type)
        st.success("Transaction Added Successfully!")

elif choice == "View Summary":
    st.subheader(f"Expense Summary for {user}")
    expenses = filter_expenses_by_period(user, "All")
    
    period_filter = st.radio("Filter by:", ["All", "Monthly", "Yearly"], index=0)
    if period_filter != "All":
        expenses = filter_expenses_by_period(user, period_filter)
    
    if expenses:
        formatted_expenses = [{"S.No": i+1, "Date": exp[1], "Category": exp[3], "Amount": exp[2]} for i, exp in enumerate(expenses)]
        st.table(formatted_expenses)
        
        total_balance = sum(exp[2] for exp in expenses)
        st.write(f"### Net Balance: ₹{total_balance}")
        
        st.subheader("Delete an Entry")
        delete_index = st.number_input("Enter the S.No of the entry to delete:", min_value=1, max_value=len(expenses), step=1)
        if st.button("Delete Entry"):
            delete_expense(user, delete_index - 1)
    else:
        st.write("No transactions recorded yet!")

st.sidebar.write("Developed with ❤️ by Moksh")

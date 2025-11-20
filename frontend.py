import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
import plotly.express as px

# --- Configuration ---
API_URL = "http://127.0.0.1:8000"  # Address where FastAPI is running

st.set_page_config(page_title="💰 Expense Tracker", layout="wide")

st.title("💰 Personal Expense Manager")

# --- Helper Functions ---
def get_categories():
    try:
        response = requests.get(f"{API_URL}/categories")
        if response.status_code == 200:
            return response.json()
    except:
        st.error("Could not connect to backend. Is FastAPI running?")
    return ["Others"]

def add_expense_api(data):
    response = requests.post(f"{API_URL}/expenses/", json=data)
    return response.status_code == 200

def get_expenses_api(start_date, end_date):
    params = {"start_date": str(start_date), "end_date": str(end_date)}
    response = requests.get(f"{API_URL}/expenses/", params=params)
    if response.status_code == 200:
        return response.json()
    return []

def get_summary_api(start_date, end_date):
    params = {"start_date": str(start_date), "end_date": str(end_date)}
    response = requests.get(f"{API_URL}/summary/", params=params)
    if response.status_code == 200:
        return response.json()
    return []

def delete_expense_api(expense_id):
    response = requests.delete(f"{API_URL}/expenses/{expense_id}")
    return response.status_code == 200

# --- Sidebar: Global Settings ---
with st.sidebar:
    st.header("📅 Filter Settings")
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    start_date = st.date_input("Start Date", first_day_of_month)
    end_date = st.date_input("End Date", today)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📋 View Expenses", "📊 Analytics"])

# --- TAB 1: Add Expense ---
with tab1:
    st.subheader("Add New Entry")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Date", today)
            amount = st.number_input("Amount ($)", min_value=0.01, format="%.2f")
        
        with col2:
            categories = get_categories()
            category = st.selectbox("Category", categories)
            subcategory = st.text_input("Subcategory (Optional)", placeholder="e.g., Uber, Groceries")
            
        note = st.text_area("Note", placeholder="Details about the expense...")
        
        submitted = st.form_submit_button("Save Expense")
        
        if submitted:
            if amount > 0:
                data = {
                    "date": str(entry_date),
                    "amount": amount,
                    "category": category,
                    "subcategory": subcategory,
                    "note": note
                }
                if add_expense_api(data):
                    st.success(f"Added ${amount} for {category}!")
                else:
                    st.error("Failed to add expense.")
            else:
                st.warning("Amount must be greater than 0.")

# --- TAB 2: View Expenses ---
with tab2:
    st.subheader(f"Expenses from {start_date} to {end_date}")
    
    expenses_data = get_expenses_api(start_date, end_date)
    
    if expenses_data:
        df = pd.DataFrame(expenses_data)
        
        # Display as dataframe with formatting
        st.dataframe(
            df,
            column_config={
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                "date": "Date",
                "category": "Category",
                "note": "Note"
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Delete functionality
        with st.expander("Delete an Expense"):
            expense_id_to_delete = st.number_input("Enter ID to delete", min_value=0, step=1)
            if st.button("Delete Expense"):
                if delete_expense_api(expense_id_to_delete):
                    st.success(f"Expense {expense_id_to_delete} deleted.")
                    st.rerun()
                else:
                    st.error("Could not delete expense. Check ID.")
    else:
        st.info("No expenses found for this date range.")

# --- TAB 3: Analytics ---
with tab3:
    st.subheader("Spending Overview")
    
    summary_data = get_summary_api(start_date, end_date)
    
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        
        # Metrics
        total_spend = df_summary['total'].sum()
        col_metrics, col_dummy = st.columns([1, 3])
        col_metrics.metric("Total Period Spending", f"${total_spend:,.2f}")
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("### By Category (Pie)")
            fig_pie = px.pie(df_summary, values='total', names='category', hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_chart2:
            st.markdown("### By Category (Bar)")
            fig_bar = px.bar(df_summary, x='category', y='total', color='category')
            st.plotly_chart(fig_bar, use_container_width=True)
            
    else:
        st.info("No data available for visualization.")
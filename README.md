# KAKEIBO - Premium Household Account Book

A modern, dark-themed household account book application built with Python and Flet.
Designed to visualize your financial flow and help you manage your budget effectively.

## ✨ Features

### 📊 Dashboard
- **Monthly Overview**: View total income, expenses, and balance for the selected month.
- **Visualizations**: Interactive pie charts showing expense breakdown by category.
- **Budget Tracking**: Monitor your spending against a monthly budget with a progress bar.
- **Recent Transactions**: List of recent entries with Edit/Delete capabilities.

### 📝 Transaction Management
- **Easy Entry**: Add income or expense records with date, category, amount, and description.
- **Smart Defaults**: Automatically selects the current date or the first day of the selected month.
- **Category Management**: Add custom categories to suit your lifestyle.

### 🌊 Money Flow (Sankey Diagram)
- **Visual Flow**: See exactly where your money goes using a Sankey diagram.
- **Income -> Total -> Expenses**: Visualize the flow from income sources to your "Total" pool, and then to expenses and savings.
- **Dynamic Layout**: Automatically adjusts to the number of categories for clear visibility.

### 🔄 Fixed Costs (Recurring Expenses)
- **Automation**: Register recurring monthly expenses (e.g., Rent, Internet, Subscriptions).
- **Auto-Add**: The app automatically checks and adds these transactions when you open it in a new month.

### ⚙️ Settings
- **Customization**: Configure application settings.
- **CSV Export**: (Coming Soon) Export your data for external analysis.

## 🚀 Installation & Running

### Prerequisites
- Python 3.12+
- `uv` package manager (recommended)

### Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   uv sync
   ```

### Running the App
```bash
uv run main.py
```

## 📖 Usage Guide

1.  **First Launch**: The app will initialize the database.
2.  **Add Transaction**: Click the "+" icon in the navigation rail. Enter details and save.
3.  **View Dashboard**: Check the Dashboard to see your balance and charts. Use the arrow buttons to switch months.
4.  **Money Flow**: Click the "Waterfall" icon to view the Sankey diagram of your finances.
5.  **Manage Fixed Costs**: Go to Settings -> Fixed Costs to register recurring payments.
6.  **Set Budget**: Click the "Edit Budget" button on the Dashboard to set your monthly spending limit.

## 🛠️ Tech Stack
- **UI Framework**: [Flet](https://flet.dev/) (Flutter for Python)
- **Database**: SQLite (via SQLAlchemy)
- **Charts**: Plotly
- **Package Manager**: uv

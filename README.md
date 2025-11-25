# KAKEIBO - Personal Finance Manager

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flet](https://img.shields.io/badge/Flet-UI-purple)
![License](https://img.shields.io/badge/License-MIT-green)

KAKEIBO is a modern, desktop-based personal finance application built with Python and Flet. It helps you track your income, expenses, and assets with a beautiful and responsive user interface.

## Features

-   **Dashboard**: Overview of your monthly balance, budget progress, and expense distribution.
-   **Transaction Management**: Easily add, edit, and delete income and expense transactions.
-   **Asset Management**: Track your total assets across multiple accounts (Bank, Cash, Investment, Stock, etc.).
-   **Money Flow**: Visualize your income and expenses flow with intuitive charts.
-   **Reports**: Analyze your spending trends and monthly comparisons.
-   **Calendar View**: View your daily financial activities on a calendar.
-   **Fixed Costs**: Manage recurring expenses like rent and subscriptions.
-   **CSV Import/Export**: Backup your data or import from other sources.
-   **Dark/Light Mode**: Choose the theme that suits your preference.

## Tech Stack

-   **Language**: Python 3.x
-   **UI Framework**: [Flet](https://flet.dev/) (Flutter for Python)
-   **Database**: SQLite (Local storage)
-   **Dependencies**:
    -   `flet`: For the user interface.
    -   `python-dateutil`: For date calculations.

## Directory Structure

```
KAKEIBO/
├── src/                # Source code
│   ├── assets/         # Static assets (icons, images)
│   ├── views/          # UI components and views
│   │   ├── dashboard.py
│   │   ├── input_form.py
│   │   ├── money_flow.py
│   │   ├── reports_view.py
│   │   ├── assets_view.py
│   │   ├── calendar_view.py
│   │   └── ...
│   ├── database.py     # Database interaction layer
│   └── main.py         # Application entry point
├── tests/              # Unit tests
│   └── test_database.py
├── .github/            # GitHub Actions workflows
├── pyproject.toml      # Project configuration
└── README.md           # Project documentation
```

## Installation & Usage

### Prerequisites

-   Python 3.10 or higher
-   [uv](https://github.com/astral-sh/uv) (Recommended for dependency management)

### Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/kakeibo.git
    cd kakeibo
    ```

2.  Install dependencies:
    ```bash
    uv sync
    ```

### Running the Application

To start the application, run:

```bash
uv run src/main.py
```

### Running Tests

To run the test suite:

```bash
uv run tests/test_database.py
```

## Build

To build the application as a standalone executable:

1.  Ensure you have the necessary build tools installed.
2.  Run the build command:
    ```bash
    flet pack src/main.py --name Kakeibo --icon src/assets/icon.ico --add-data "src/assets;assets"
    ```
    *Note: You may need to adjust the path to `icon.ico` and assets depending on your environment.*

3.  The executable will be generated in the `dist` directory.

## License

This project is licensed under the MIT License.

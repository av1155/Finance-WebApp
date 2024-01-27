# StockfolioHub

## Introduction

StockfolioHub is an innovative full-stack web application that leverages the power of the IEX API to provide users with real-time trading data and a seamless trading experience. It is developed using Python, Flask, HTML, JavaScript, CSS, and Bootstrap. The application offers a straightforward functionality that simplifies the stock trading process, making it accessible to users of all levels of experience.

## Features

### Account Management

-   **Account Registration**: Users can easily register accounts and log in.
-   **Secure Data Storage**: Account data is stored securely in an SQLite database.

### Stock Trading

-   **Real-Time Data**: Utilizes the IEX API for real-time stock information.
-   **Trading Functionality**: Users can buy and sell stocks, managing their portfolio directly on the website.

### User Interface

-   **Intuitive Design**: The platform offers an intuitive interface for a smooth user experience.
-   **Bootstrap Integration**: Utilizes Bootstrap for responsive design and attractive UI components.

## Usage Guide

1.  **Account Registration**: Sign up for a new account to access the platform.
2.  **Stock Quotation**: Check real-time prices of stocks using the 'Quote' feature.
3.  **Trading Stocks**: Use 'Buy' and 'Sell' features to trade stocks.
4.  **Portfolio Review**: View your current holdings and their values on the homepage.
5.  **Reviewing Transactions**: Access your transaction history under 'History'.
6.  **Cash Management**: Add funds to your account using 'Add Cash'.

## Files Overview

-   `app.py`: Main Flask application file.
-   `finance.db`: SQLite database for user data and transactions.
-   `helpers.py`: Contains helper functions for various operations.
-   `requirements.txt`: Required Python packages.
-   `static/`: Static files like CSS and favicon.
-   `templates/`: HTML templates for the web pages.

## Hosting

-   **Heroku Deployment**: Hosted on Heroku for ease of access and reliability.

## Data Sources

-   **IEX Cloud**: Data provided by IEX Cloud for up-to-date stock information.

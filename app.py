from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query user's stock holdings and cash balance
    stocks = db.execute(
        "SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        session["user_id"],
    )
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0][
        "cash"
    ]

    # Update each stock's current price and total value
    holdings = []
    grand_total = cash
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["total"] = stock["total_shares"] * quote["price"]
        grand_total += stock["total"]
        holdings.append(stock)

    return render_template(
        "index.html", stocks=holdings, cash=cash, grand_total=grand_total
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")

        if not symbol or not shares:
            return apology("Missing symbol or shares")

        try:
            shares = int(shares)
        except ValueError:
            return apology("Shares must be a positive integer")

        if shares <= 0:
            return apology("Shares must be a positive integer")

        stock = lookup(symbol)
        if not stock:
            return apology("Invalid symbol")

        # Check user's current cash
        rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = rows[0]["cash"]

        total_cost = shares * stock["price"]
        if cash < total_cost:
            return apology("Not enough cash")

        # Update user's cash
        db.execute(
            "UPDATE users SET cash = cash - ? WHERE id = ?",
            total_cost,
            session["user_id"],
        )

        # Record the transaction
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, 'buy')",
            session["user_id"],
            stock["symbol"],
            shares,
            stock["price"],
        )

        flash("Bought!")
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT symbol, shares, price, type, timestamp FROM transactions WHERE user_id = ?",
        session["user_id"],
    )
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Symbol is required")

        stock = lookup(symbol)
        if not stock:
            return apology("Invalid symbol")

        # Render quoted page with stock info
        return render_template(
            "quoted.html",
            name=stock["name"],
            symbol=stock["symbol"],
            price=stock["price"],
        )

    # User reached route via GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (submitting the form)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username, password, and confirmation are submitted
        if not username or not password or not confirmation:
            return apology("Must provide username and password")

        # Ensure password and confirmation match
        if password != confirmation:
            return apology("Passwords do not match")

        # Check if username already exists
        if db.execute("SELECT * FROM users WHERE username = ?", username):
            return apology("Username already taken")

        # Add password complexity validation
        if not is_password_complex(password):
            return apology(
                "Password must contain uppercase, lowercase, numbers, special characters, and be at least 8 characters long"
            )

        # Hash password and insert new user into the database
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        # Redirect to login page or log the user in directly
        return redirect("/login")

    # User reached route via GET (as by clicking a link or redirect)
    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Add password complexity validation
        if not is_password_complex(new_password):
            return apology(
                "Password must contain uppercase, lowercase, numbers, special characters, and be at least 8 characters long"
            )

        # Query database for old password
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Ensure old password is correct
        if not check_password_hash(user[0]["hash"], old_password):
            return apology("Invalid old password", 403)

        # Ensure new password and confirmation match
        if new_password != confirmation:
            return apology("Passwords do not match", 403)

        # Update user's password in the database
        new_hash = generate_password_hash(new_password)
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"]
        )

        flash("Password changed successfully!")
        return redirect("/")
    else:
        return render_template("change_password.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        shares = int(request.form.get("shares"))

        if not symbol or shares <= 0:
            return apology("Invalid symbol or number of shares")

        # Check user's shares of the stock
        stock_shares = db.execute(
            "SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol",
            session["user_id"],
            symbol,
        )[0]["total_shares"]
        if shares > stock_shares:
            return apology("Too many shares")

        # Update user's cash and record the transaction
        stock = lookup(symbol)
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            shares * stock["price"],
            session["user_id"],
        )
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, 'sell')",
            session["user_id"],
            symbol,
            -shares,
            stock["price"],
        )

        flash("Sold!")
        return redirect("/")

    else:
        # Get user's stock symbols for the dropdown
        symbols = db.execute(
            "SELECT DISTINCT symbol FROM transactions WHERE user_id = ?",
            session["user_id"],
        )
        return render_template("sell.html", symbols=symbols)


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    if request.method == "POST":
        additional_cash = request.form.get("cash")

        # Validation and conversion to float
        try:
            additional_cash = float(additional_cash)
            if additional_cash <= 0:
                return apology("Amount must be positive", 403)
        except ValueError:
            return apology("Invalid amount", 403)

        # Update cash in users table
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?",
            additional_cash,
            session["user_id"],
        )

        flash("Cash added successfully!")
        return redirect("/")

    else:
        return render_template("add_cash.html")


def is_password_complex(password):
    if len(password) < 8:
        return False

    has_upper = has_lower = has_digit = has_special = False

    for char in password:
        if char.isdigit():
            has_digit = True
        elif char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char in "@$!%*?&_.":
            has_special = True

    return all([has_upper, has_lower, has_digit, has_special])

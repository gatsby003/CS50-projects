import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

print(os.environ.get("API_KEY"))
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    db_query = db.execute("SELECT stock, qty FROM users JOIN records ON id=user_id WHERE user_id=:id", id=session["user_id"])
    clean_list = []
    cash = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"]
    total = cash
    # prepare a clean list of values for preparing table on index page
    for i in range(len(db_query)):
        api_query = lookup(db_query[i]["stock"])
        share_no = db_query[i]["qty"]
        total_share_price = int(share_no) * api_query["price"]
        clean_list.append({"symbol": db_query[i]["stock"],
                        "name": api_query["name"],
                        "share": share_no,
                        "price": api_query["price"],
                        "total": total_share_price})
        total += total_share_price
    return render_template("index.html", input_list=clean_list, cash=round(cash,2), total=round(total,2))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # check if stock exists
        if lookup(request.form.get("symbol")) == None:
            return apology("Enter Valid Symbol")
        # query cash
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        # query share symbol
        share = lookup(request.form.get("symbol"))["symbol"]
        # query stock price
        stock_quote = lookup(request.form.get("symbol"))["price"]
        # query stock qty
        qty = request.form.get("shares")
        # calculate stock price
        cost = stock_quote * int(qty)
        # calculate cash left
        cash_left = cash[0]["cash"] - cost
        # if not enough cash available
        if cash[0]["cash"] < cost:
            return apology("Not Enough Cash")
        # sql queries for updating db
        db.execute("UPDATE users SET cash = :cash WHERE id=:id",cash=cash_left,id=session["user_id"])
        db.execute("INSERT INTO orders (user_id, share, qty, price, type, time) VALUES (:id, :share, :qty, :price, :type, :time)",id=session["user_id"], share=share, qty=qty, price=cost, type="Buy", time=datetime.now())
        # update records table of portfolio
        if (db.execute("SELECT * FROM records WHERE user_id=:id AND stock=:stock", id=session["user_id"],stock=share) == []):
            db.execute("INSERT INTO records (user_id, stock, qty) VALUES (:id, :stock, :qty)", id=session["user_id"],stock=share,qty=qty)
        else:
            db.execute("UPDATE records SET qty = qty + :qty WHERE user_id=:id AND stock=:stock", qty=qty, id=session["user_id"], stock=share)
        flash("Success!")
        # redirect to index page with record of portfolio shown
        return redirect("/")
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    order_query = db.execute("SELECT * FROM orders WHERE user_id=:id", id=session["user_id"])
    return render_template("history.html", data=order_query)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
        # checks for invalid symbol
        if (lookup(request.form.get("symbol")) == None):
            flash("Invalid Symbol")
            return apology("Invalid Symbol", 401)
        # else returns rendered template
        return render_template("quoted.html", lookup=lookup(request.form.get("symbol")))
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Enter Valid Username", 403)
        if not request.form.get("password"):
            return apology("Enter Valid Password", 403)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 402)

        # ensuring unique usernames
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) == 1:
            flash("Username Already Exists")
            return redirect("/register")
        # user registeration
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)",
                   username=request.form.get("username"),
                   password=generate_password_hash(request.form.get("password")))
        return redirect("/")
    else:
        flash("Only Alphanumeric Passwords Accepted")
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    sql_query = db.execute("SELECT stock, qty FROM records WHERE user_id=:id", id = session["user_id"])
    clean_list = []
    # storing the items of select menu in a list
    for i in range(len(sql_query)):
        clean_list.append(sql_query[i]["stock"])
    if request.method == "POST":
        share = request.form.get("select")
        qty = int(request.form.get("shares"))
        qty_query = db.execute("SELECT qty FROM records WHERE user_id=:id AND stock=:share", id=session["user_id"], share=share)
        # quantity of shares the user holds
        real_qty = int(qty_query[0]["qty"])
        # the value of the said shares
        selling_price = lookup(share)["price"] * qty
        # error checking if user sells more than he owns
        if qty > real_qty:
            flash("Too many shares selected")
            return render_template("sell.html")
        # insert a selling order in orders table
        db.execute("INSERT INTO orders (user_id, share, qty, price, type, time) VALUES (:id, :share, :qty, :price, :type, :time)", id=session["user_id"], share=share, qty=qty, price=selling_price, type="Sell", time=datetime.now())
        # deletes the row if after selling the qty == 0
        if (real_qty == qty):
            db.execute("DELETE FROM records WHERE user_id=:id AND stock=:share", id=session["user_id"], share=share)
        else:
            db.execute("UPDATE records SET qty= qty - :qty WHERE user_id=:id AND stock=:share" , id=session["user_id"], share=share, qty=qty)
        # updating the cash holding of the user after the sale
        db.execute("UPDATE users SET cash=cash + :cash WHERE id=:id", id=session["user_id"], cash=selling_price)
        return redirect("/")
    else:
        return render_template("sell.html",clean_list=clean_list)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

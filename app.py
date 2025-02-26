import random
import string
from flask import Flask, request, redirect, render_template, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Needed for flash messages

db = SQLAlchemy(app)

# Database Model
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)  # Track number of clicks

# Generate a random short code (Ensuring it's unique)
def generate_short_code():
    while True:
        short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not URL.query.filter_by(short_code=short_code).first():  # Ensure uniqueness
            return short_code

# Home Route
@app.route("/", methods=["GET", "POST"])
def home():
    short_url = None
    if request.method == "POST":
        long_url = request.form["long_url"].strip()
        custom_code = request.form.get("custom_code", "").strip()

        # Prevent duplicate long URLs
        existing_url = URL.query.filter_by(long_url=long_url).first()
        if existing_url:
            short_url = f"http://127.0.0.1:5000/{existing_url.short_code}"
            flash(f"Shortened URL already exists: <a href='{short_url}' target='_blank'>{short_url}</a>", "info")
            return render_template("index.html", short_url=short_url)

        # Check if custom code is provided and unique
        if custom_code:
            if URL.query.filter_by(short_code=custom_code).first():
                flash("Error: Custom short code already taken! Try another.", "danger")
                return redirect(url_for("home"))
            short_code = custom_code
        else:
            short_code = generate_short_code()

        # Save to database
        new_url = URL(long_url=long_url, short_code=short_code)
        db.session.add(new_url)
        db.session.commit()

        short_url = f"http://127.0.0.1:5000/{short_code}"
        flash(f"Shortened URL: <a href='{short_url}' target='_blank'>{short_url}</a>", "success")
        return render_template("index.html", short_url=short_url)

    return render_template("index.html", short_url=short_url)

# Redirect Route (Increments Click Counter)
@app.route("/<short_code>")
def redirect_to_long(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first()
    if url_entry:
        url_entry.clicks += 1  # Increase click count
        db.session.commit()
        return redirect(url_entry.long_url)
    
    flash("Invalid short URL!", "danger")
    return redirect(url_for("home"))

# Route to Show All Shortened URLs
@app.route("/all-urls")
def all_urls():
    urls = URL.query.all()
    return render_template("all_urls.html", urls=urls)

# Run the Flask App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

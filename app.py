import math
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash  # Import hashing utilities
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:9260786921@localhost/medicine_finder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define the haversine function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in km

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Define the Pharmacy model
class Pharmacy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    available_medicines = db.Column(db.String(500), nullable=True)
    timings = db.Column(db.String(100), nullable=True)  # Timings of the pharmacy
    contact_number = db.Column(db.String(20), nullable=True)  # Contact number
    latitude = db.Column(db.Float, nullable=True)  # Latitude of the pharmacy
    longitude = db.Column(db.Float, nullable=True)  # Longitude of the pharmacy

with app.app_context():
    # Fetch pharmacy data from the database
    pharmacies = Pharmacy.query.all()  # Uncommented to fetch pharmacy data after migration

# Create a dictionary to hold pharmacy data
medicals = {pharmacy.name: pharmacy.available_medicines.split(', ') for pharmacy in pharmacies}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    medicine = request.form.get('medicine').strip()
    print(f"Searched medicine: {medicine}")  # Debug print

    # Get all pharmacies and check if the searched medicine is available
    matching_pharmacies = []
    pharmacies = Pharmacy.query.all()
    for pharmacy in pharmacies:
        available_meds = [med.strip().lower() for med in pharmacy.available_medicines.split(',')]  # Split and trim medicines
        if medicine.lower() in available_meds:  # Case insensitive match
            matching_pharmacies.append(pharmacy)

    # Proceed with location and distance logic
    user_lat_str = request.form.get('latitude')
    user_lon_str = request.form.get('longitude')

    if not user_lat_str or not user_lon_str:
        return "Could not obtain your location. Please try again.", 400
    
    try:
        user_lat = float(user_lat_str)
        user_lon = float(user_lon_str)
    except ValueError:
        return "Invalid location data received.", 400
    
    pharmacies_with_distance = []
    for pharmacy in matching_pharmacies:
        if pharmacy.latitude and pharmacy.longitude:
            distance = haversine(user_lat, user_lon, pharmacy.latitude, pharmacy.longitude)
            pharmacies_with_distance.append({
                'pharmacy': pharmacy,
                'distance': round(distance, 2)
            })

    if not pharmacies_with_distance:
        return render_template('search_results.html', medicine=medicine, pharmacies=[], message="No pharmacies found with this medicine.")
    
    return render_template('search_results.html', medicine=medicine, pharmacies=pharmacies_with_distance)

@app.route('/add_pharmacy', methods=['GET', 'POST'])
def add_pharmacy():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        available_medicines = request.form['available_medicines']
        timings = request.form['timings']  # Get timings from the form
        contact_number = request.form['contact_number']  # Get contact number from the form
        latitude = request.form.get('latitude', type=float)  # Get latitude from form and convert to float
        longitude = request.form.get('longitude', type=float)  # Get longitude from form and convert to float

        # Create a new Pharmacy instance with latitude and longitude
        new_pharmacy = Pharmacy(
            name=name, 
            address=address, 
            available_medicines=available_medicines, 
            timings=timings, 
            contact_number=contact_number,
            latitude=latitude,
            longitude=longitude
        )
        
        db.session.add(new_pharmacy)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_pharmacy.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query for the user in the database
        user = User.query.filter_by(username=username).first()
        
        # Check if the user exists and the password is correct
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid credentials! Please try again."
            return render_template('login.html', error=error)  # Pass error to template

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = "Username already exists. Please choose another one."
            return render_template('signup.html', error=error)

        # Create a new user with a hashed password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        
        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('data'):
        os.makedirs('data')
    app.run(debug=True)

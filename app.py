import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
from flask_cors import CORS
import random
from twilio.rest import Client
from flask_bcrypt import Bcrypt
import pickle

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Ensure that the DATABASE_URL is properly defined
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("No DATABASE_URL found in environment variables.")

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
app.app_context().push()


# Database model for Users
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def _repr_(self) -> str:
        return f"<User {self.username}>"


# Function to create the database tables
def create_db():
    with app.app_context():
        db.create_all()

# Routes for homepage, user creation, and form submission
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password_hash = generate_password_hash(request.form['password'])
        full_name = request.form.get('full_name', '')
        phone_number = request.form.get('phone_number', '')
        address = request.form.get('address', '')

        user = Users(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone_number=phone_number,
            address=address,
        )
        db.session.add(user)
        db.session.commit()
    
    all_users = Users.query.all()
    return render_template('index.html', allUsers=all_users)

# Route for updating user information
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    user = Users.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.password_hash = generate_password_hash(request.form['password'])
        user.full_name = request.form.get('full_name', user.full_name)
        user.phone_number = request.form.get('phone_number', user.phone_number)
        user.address = request.form.get('address', user.address)

        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('update.html', user=user)

# Route for deleting a user
@app.route('/delete/<int:id>')
def delete_user(id):
    user = Users.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('index'))

# Route to render login page
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = Users.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['user_name'] = user.username
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

# Logout route to clear the session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Route to render the registration page
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/contact', methods=['GET'])
def contact_page():
    return render_template('contact.html')


# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('ACCOUNT_SID') # Replace with your Twilio account SID
TWILIO_AUTH_TOKEN = os.getenv('AUTH_TOKEN')      # Replace with your Twilio auth token
TWILIO_PHONE_NUMBER = os.getenv('PHONE_NUMBER')  # Replace with your Twilio Phone Number
TWILIO_VERIFY_SERVICE_SID = os.getenv('VERIFY_SERVICE_SID')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Route to handle registration form submission
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number')

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already registered'}), 400

    try:
        verification = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone_number,
            channel='sms'
        )

        session['pending_user'] = {
            'full_name': full_name,
            'email': email,
            'password': password,
            'phone_number': phone_number
        }

        return jsonify({'success': True, 'message': 'OTP sent successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/verify_phone', methods=['POST'])
def verify_phone():
    data = request.get_json()
    phone_number = data.get('phone_number')
    code = data.get('code')

    try:
        verification_check = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=phone_number,
            code=code
        )

        if verification_check.status == 'approved':
            pending_user = session.get('pending_user')

            if pending_user and pending_user['phone_number'] == phone_number:
                new_user = Users(
                    username=pending_user['email'].split('@')[0],
                    email=pending_user['email'],
                    password_hash=generate_password_hash(pending_user['password']),
                    full_name=pending_user['full_name'],
                    phone_number=phone_number
                )

                db.session.add(new_user)
                db.session.commit()
                session.pop('pending_user', None)  # Clear pending user data

                return jsonify({'success': True, 'message': 'Registration complete'}), 200
            else:
                return jsonify({'success': False, 'message': 'No matching pending user found'}), 404
        else:
            return jsonify({'success': False, 'message': 'Invalid OTP'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    
# Routes
@app.route('/forget_password')
def forget_password():
    return render_template('forget_password.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        phone = data.get('email_or_phone')

        if not phone:
            return jsonify({"success": False, "error": "Phone number is required."}), 400

        user = Users.query.filter_by(phone_number=phone).first()
        if not user:
            return jsonify({"success": False, "error": "User not found."}), 404

        otp = str(random.randint(100000, 999999))
        otp_store[phone] = otp

        try:
            twilio_client.messages.create(
                body=f'HosPet Security: Your OTP is {otp}',
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )
        except Exception as e:
            print(f"Twilio Error: {e}")
            return jsonify({"success": False, "error": "Failed to send OTP. Please try again."}), 500

        return jsonify({"success": True, "otp": otp}), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

@app.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.form
        phone = data.get('email_or_phone')
        new_password = data.get('new_password')

        user = Users.query.filter_by(phone_number=phone).first()
        if not user:
            return "User not found", 404

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()

        return "Password reset successful", 200

    except Exception as e:
        print(f"Server Error: {e}")
        return "Internal Server Error", 500


# Route to render the profile page
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('profile.html')

# API endpoint to fetch profile data
@app.route('/api/profile')
def get_profile_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized access'}), 401

    user_id = session['user_id']
    user = Users.query.get(user_id)

    if user:
        return jsonify({
            'full_name': user.full_name,
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number
        })
    else:
        return jsonify({'error': 'User not found'}), 404



# Example data for animal medicines (In a real application, this data should come from a database)
medicines = {
"Paracetamol": "<b>Paracetamol</b> <br> <br> Description:<br> Used for pain relief in dogs. <br> It helps manage fever and minor aches. <br> <br> Caution: Paracetamol is highly toxic to cats and should never be given without strict veterinary guidance.",
"Aspirin": "<b>Aspirin</b> <br> <br> Description:<br> An anti-inflammatory drug used for pain relief and reducing inflammation in dogs. <br> It can be used for mild to moderate pain, but long-term use should be avoided due to potential gastrointestinal issues. <br> Not recommended for use in cats.",
"Ibuprofen": "<b>Ibuprofen</b> <br> <br> Description:<br> A nonsteroidal anti-inflammatory drug (NSAID) occasionally used for pain relief but generally not recommended for pets due to high toxicity risks, particularly in cats. <br> Consult a veterinarian before use.",
"Amoxicillin": "<b>Amoxicillin</b> <br> <br> Description:<br> A broad-spectrum antibiotic effective for treating various bacterial infections in animals, including skin, respiratory, and urinary tract infections. <br> Safe under veterinary guidance.",
"Metronidazole": "<b>Metronidazole</b> <br> <br> Description:<br> Commonly used to treat infections in cats and dogs, especially gastrointestinal infections and certain bacterial overgrowths. <br> It has anti-inflammatory properties that help in reducing gut inflammation.",
"Corticosteroids": "<b>Corticosteroids</b> <br> <br> Description:<br> A class of drugs used to reduce inflammation and suppress the immune response in pets. <br> Effective for treating allergies, autoimmune diseases, and other inflammatory conditions. <br> Long-term use may lead to side effects like increased thirst and weight gain.",
"Furosemide": "<b>Furosemide</b> <br> <br> Description:<br> A diuretic medication used to treat fluid retention and edema due to heart conditions in dogs and cats. <br> Helps reduce the workload on the heart by removing excess fluid through urination.",
"Dexamethasone": "<b>Dexamethasone</b> <br> <br> Description:<br> A potent corticosteroid used for severe allergies, inflammation, and immune-mediated diseases in pets. <br> Also used in emergency treatments for shock or adrenal insufficiency.",
"Carprofen": "<b>Carprofen</b> <br> <br> Description:<br> An NSAID specifically used for pain relief and inflammation control in dogs, often prescribed for osteoarthritis and post-surgical recovery. <br> Should be used under veterinary supervision.",
"Gabapentin": "<b>Gabapentin</b> <br> <br> Description:<br> Used for pain relief, especially in cases of neuropathic pain, and to manage seizures in both dogs and cats. <br> Can also be used to ease anxiety and stress in pets.",
"Phenobarbital": "<b>Phenobarbital</b> <br> <br> Description:<br> An anticonvulsant drug commonly prescribed for the long-term management of epilepsy and seizures in dogs and cats. <br> Regular blood tests are recommended to monitor liver function.",
"Acepromazine": "<b>Acepromazine</b> <br> <br> Description:<br> A sedative and anti-nausea drug used to manage anxiety, fear-related behaviors, and motion sickness in animals. <br> Can be helpful for pets during travel or stressful events.",
"Clavamox": "<b>Clavamox</b> <br> <br> Description:<br> A combination antibiotic that contains amoxicillin and clavulanic acid, used for treating a range of bacterial infections in dogs and cats, such as skin and soft tissue infections.",
"Trazodone": "<b>Trazodone</b> <br> <br> Description:<br> An antidepressant that is often prescribed to manage anxiety and behavioral issues in dogs. <br> Also used as a sedative to help pets relax during stressful situations.",
"Tramadol": "<b>Tramadol</b> <br> <br> Description:<br> A pain reliever used to treat moderate to severe pain in dogs and cats. <br> Works similarly to opioid pain medications and is sometimes used in combination with other pain management treatments.",
"Cimetidine": "<b>Cimetidine</b> <br> <br> Description:<br> A medication used to treat stomach ulcers and manage acid reflux in pets. <br> Helps reduce the amount of acid in the stomach, promoting healing of the gastrointestinal tract.",
"Omeprazole": "<b>Omeprazole</b> <br> <br> Description:<br> A proton pump inhibitor that decreases the production of stomach acid, used for treating gastrointestinal conditions such as ulcers and acid reflux in dogs and cats.",
"Loperamide": "<b>Loperamide</b> <br> <br> Description:<br> An anti-diarrheal medication used in dogs to control symptoms of diarrhea. <br> Should only be used under veterinary supervision, as it is unsafe for use in cats.",
"Meloxicam": "<b>Meloxicam</b> <br> <br> Description:<br> An NSAID used for pain relief and to reduce inflammation in dogs and cats. <br> Commonly prescribed for osteoarthritis and other musculoskeletal disorders.",
"Enalapril": "<b>Enalapril</b> <br> <br> Description:<br> An ACE inhibitor used for treating heart failure and high blood pressure in dogs. <br> Helps relax blood vessels and improve blood flow, easing the strain on the heart.",
"Hydrochlorothiazide": "<b>Hydrochlorothiazide</b> <br> <br> Description:<br> A diuretic used to manage high blood pressure and fluid retention (edema) in dogs. <br> Works by promoting urine production to expel excess fluid.",
"Insulin": "<b>Insulin</b> <br> <br> Description:<br> Used to manage diabetes in dogs and cats by controlling blood sugar levels. <br> Dosage must be carefully managed and monitored under veterinary care.",
"Glucosamine": "<b>Glucosamine</b> <br> <br> Description:<br> A nutritional supplement used to support joint health and cartilage repair in aging pets, especially beneficial for dogs with osteoarthritis.",
"Amlodipine": "<b>Amlodipine</b> <br> <br> Description:<br> A calcium channel blocker used to treat hypertension (high blood pressure) in cats. <br> Helps relax and widen blood vessels for better blood flow.",
"Ciprofloxacin": "<b>Ciprofloxacin</b> <br> <br> Description:<br> A broad-spectrum antibiotic used to treat various infections in pets, including skin and respiratory infections. <br> Should be prescribed by a veterinarian.",
"Itraconazole": "<b>Itraconazole</b> <br> <br> Description:<br> An antifungal medication used to treat fungal infections in dogs and cats, such as ringworm and blastomycosis. <br> May require long-term treatment.",
"Fentanyl": "<b>Fentanyl</b> <br> <br> Description:<br> A powerful opioid pain medication used for severe pain management in pets. <br> Often administered through patches for controlled, long-lasting relief.",
"Zylkene": "<b>Zylkene</b> <br> <br> Description:<br> A natural supplement derived from milk protein that promotes calming effects and reduces anxiety in pets. <br> Suitable for stressful situations like travel and loud noises.",
"Lactulose": "<b>Lactulose</b> <br> <br> Description:<br> A stool softener used to treat constipation in cats and dogs. <br> Also used in the treatment of liver disease to reduce ammonia levels in the blood.",
"Nitroglycerin": "<b>Nitroglycerin</b> <br> <br> Description:<br> Used for treating heart conditions in pets, particularly to manage congestive heart failure. <br> Applied as a topical ointment or patch.",
"Clofibric acid": "<b>Clofibric acid</b> <br> <br> Description:<br> Used to help manage high cholesterol levels in dogs. <br> Typically part of a broader treatment plan that includes diet adjustments.",
"Metoclopramide": "<b>Metoclopramide</b> <br> <br> Description:<br> An anti-nausea and prokinetic medication used to promote movement of the stomach and intestines in pets, easing symptoms of nausea and vomiting.",
"Probiotics": "<b>Probiotics</b> <br> <br> Description:<br> Supplements that support digestive health and help maintain a balanced gut flora in pets. <br> Useful for managing digestive issues and enhancing overall gut health.",
"Ketoconazole": "<b>Ketoconazole</b> <br> <br> Description:<br> An antifungal medication used for treating skin and systemic fungal infections in dogs and cats. <br> May have side effects with prolonged use.",
"Desoxycorticosterone": "<b>Desoxycorticosterone</b> <br> <br> Description:<br> A hormonal treatment used in managing Addison's disease in dogs by supplementing necessary adrenal hormones.",

    # Add more medicines as needed
}
@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    return render_template('medicine.html')  # Render the medicinal info page

@app.route('/search_medicine', methods=['POST'])
def search_medicine():
    medicine_name = request.form.get('medicine').strip().lower()  # Normalize input to lowercase
    # Use a dictionary comprehension to create a case-insensitive lookup
    normalized_medicines = {key.lower(): value for key, value in medicines.items()}
    info = normalized_medicines.get(medicine_name, "No information found for this medicine.")
    return jsonify({"info": info})


@app.route('/hospitals')
def hospitals():
    return render_template('hospitals.html')

@app.route('/hospitals', methods=['GET','POST'])
def get_hospitals():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    overpass_query = f"""
    [out:json];
    (
        node[amenity=veterinary](around:5000, {latitude}, {longitude});
        node[amenity=animal_shelter](around:5000, {latitude}, {longitude});
        node[amenity=pet_care](around:5000, {latitude}, {longitude});
    );
    out;
    """

    response = requests.get(f'https://overpass-api.de/api/interpreter?data={overpass_query}')
    if response.status_code == 200:
        data = response.json()
        return jsonify(data['elements'])
    else:
        return jsonify({'error': 'Failed to fetch data'}), 500



@app.route('/video_call')
def video_call():
    return render_template('video_call.html')


# ML model

# Load the trained model and label encoder using pickle
with open('disease_prediction_model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('label_encoder.pkl', 'rb') as encoder_file:
    label_encoder = pickle.load(encoder_file)

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'No input data provided'}), 400

    age = data.get('age')
    temperature = data.get('temperature')
    symptom1 = data.get('symptom1', '')
    symptom2 = data.get('symptom2', '')
    symptom3 = data.get('symptom3', '')

    # Combine symptoms into a single string
    symptoms = ' '.join([symptom1, symptom2, symptom3]).strip()
    description = data.get('description', '')

    if not symptoms:
        return jsonify({'error': 'Symptoms are required for prediction'}), 400

    # Prepare input data for prediction
    input_data = [symptoms]

    # Handle the image upload
    image = request.files.get('image')
    if image and image.filename != '':
        image_data = image.read()  # Read the image data as binary
        print(f"Image read successfully: {len(image_data)} bytes")  # Log the image size for confirmation
    else:
        print("No image uploaded or image is empty")
        image_data = None



    try:
        # Make prediction
        disease_encoded = model.predict(input_data)[0]
        disease = label_encoder.inverse_transform([disease_encoded])[0]

        # Save the data in the SQLite database
        # new_report = Report(
        #     age=age,
        #     temperature=temperature,
        #     symptoms=symptoms,
        #     description=description,
        #     predicted_disease=disease,
        #     image=image_data
        # )
        # db.session.add(new_report)
        # db.session.commit()

        # Return the result as a JSON response
        return jsonify({'predicted_disease': disease})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

#chatbot app.py

import google.generativeai as genai
import json
import re

# Configure the Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Load Gemini model
gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
chat = gemini_model.start_chat(history=[])

conversation_file = 'conversations.json'

def load_conversations():
    if os.path.exists(conversation_file):
        with open(conversation_file, 'r') as f:
            return json.load(f)
    return {}

def save_conversation(user_input, response):
    conversations = load_conversations()
    conversations[user_input] = response
    with open(conversation_file, 'w') as f:
        json.dump(conversations, f, indent=4)

def get_gemini_response(user_input):
    response = chat.send_message(user_input, stream=True)
    full_response = ""
    for chunk in response:
        full_response += chunk.text
    save_conversation(user_input, full_response)
    return full_response

@app.route('/HosBot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_input = request.json.get('message')
    conversations = load_conversations()

    if user_input in conversations:
        response = conversations[user_input]
    else:
        response = get_gemini_response(user_input)
        response = re.sub(r"\*", "", response)
    
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run()
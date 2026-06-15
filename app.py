from flask import Flask, jsonify, render_template, request,redirect,url_for,session
from flask_cors import CORS
import mysql.connector
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
import requests

import os






app = Flask(__name__)
CORS(app)

app.secret_key = "college_nav_secret_123"
# ---------------- DATABASE ----------------

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="RS12@shrey",
        database="college_nav"
    )
except mysql.connector.Error as err:
    print("DB Error:", err)
    db = None






# ---------------- FAQ FUNCTIONS ----------------
def load_faq():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT question, answer FROM faq")
    faq_data = {row["question"].lower(): row["answer"] for row in cursor.fetchall()}
    cursor.close()
    return faq_data

faq_data = load_faq()
faq_questions = list(faq_data.keys())
faq_answers = list(faq_data.values())
def faq_response(user_query):
    user_query = user_query.lower()



    # ✅ TF-IDF fallback
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(faq_questions + [user_query])
    similarity_scores = cosine_similarity(vectors[-1], vectors[:-1])
    idx = similarity_scores.argmax()

    if similarity_scores[0][idx] > 0.4:   # lower threshold
        return faq_answers[idx]

    return None




def ask_deepseek(prompt):
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 40,     # limit output → faster
            "temperature": 0.2,    # less randomness → accurate
            "top_p": 0.9
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)

        print("STATUS:", response.status_code)
        print("RAW RESPONSE:", response.text)

        result = response.json()

        return result.get("response", "").strip()

    except Exception as e:
        print("ERROR:", e)
        return None

    


# ---------------- CAMPUS KEYWORDS ----------------

CAMPUS_KEYWORDS = [
    "college", "campus", "library", "office", "canteen", "hostel",
    "lab", "department", "classroom", "fees", "exam",
    "principal", "admission", "timing", "bus",
    "parking", "wifi", "sports", "ground",
    "map", "location", "where", "how to reach",
    "admin", "attendance", "syllabus"
]


def is_campus_related(question):

    q = question.lower()

    return any(word in q for word in CAMPUS_KEYWORDS)

def clean_place(text):

    remove_words = [
        "where is", "where", "located", "location of",
        "show me", "tell me", "please", "?", "."
    ]

    text = text.lower()

    for word in remove_words:
        text = text.replace(word, "")

    return text.strip()



# ---------------- ROUTES ----------------


@app.route("/")
def home():
    if "username" in session:
        return render_template("index.html", username=session["username"])
    return redirect(url_for("login"))

#--------------------------------------------------------------#


def find_location(place):

    cursor = db.cursor(dictionary=True)

    query = """
    SELECT location, latitude, longitude
    FROM locations
    WHERE LOWER(location) LIKE %s
    LIMIT 1
    """

    cursor.execute(query, ("%" + place.lower() + "%",))

    result = cursor.fetchone()

    cursor.close()

    return result


def extract_place(question):

    words = question.lower().split()

    ignore = ["where", "is", "the", "a", "an", "of", "please"]

    place = [w for w in words if w not in ignore]

    return " ".join(place)


# ---------- Location API ----------

@app.route("/locations", methods=["GET"])
def get_locations():

    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    db.reconnect(attempts=1, delay=0)

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, location,
        ROUND(latitude,5) AS latitude,
        ROUND(longitude,5) AS longitude
        FROM locations
    """)

    data = cursor.fetchall()

    cursor.close()

    return jsonify(data)


# ---------- Chatbot API ----------

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"reply": "Please type something."})
    
    msg = user_message.lower()


    # 🔹 1. LOCATION FIRST (FIX)
    if "where is" in user_message.lower():
        place = extract_place(user_message)
        location = find_location(place)

        if location:
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["location"]

            map_link = f"https://www.google.com/maps?q={lat},{lon}"

            reply = f"""📍 <b>{name}</b><br>
            <a href="{map_link}" target="_blank">👉 Open in Google Maps</a>"""

            return jsonify({"reply": reply})
    
        # ❗ IMPORTANT: DO NOT RETURN HERE
        print("Location not found → fallback to AI")


    # 🔹 2. FAQ
    faq_answer = faq_response(user_message)
    if faq_answer:
        return jsonify({"reply": faq_answer})

    
        # 🔹 3. AI (Ollama DeepSeek)
    if is_campus_related(user_message):

        campus_context = f"""
        You are a campus navigation assistant.

        STRICT RULES:
        - Answer ONLY using given campus info
        - Do NOT think step-by-step
        - Do NOT explain reasoning
        - Keep answer short (1-2 lines only)
        - If not related, say: "Ask campus-related question only"

        Campus Info:
        - Library is near Block A
        - Canteen is near Gate 2
        - Computer Department is in Block C
        - Admin office near main entrance
        - Parking near Gate 1

        User Question: {user_message}

        Answer:
        """


    
    reply = ask_deepseek(campus_context)

     # ✅ ADD DEBUG HERE
    print("USER:", user_message)
    print("AI REPLY:", reply)

    if reply and reply.strip():
            return jsonify({"reply": reply.strip()})
    else:
            return jsonify({"reply": "⚠️ AI not responding"})

    # 🔹 4. FINAL FALLBACK
    return jsonify({"reply": "Ask campus-related question only."})

   


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            if check_password_hash(user["password"], password):
                name = email.split("@")[0]
                return render_template("index.html",username=name)  # ✅ directly open index
            else:
                return "Wrong Password!"
        else:
            return "No account found. Please Sign Up."

    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            return "Account already exists. Please login."

        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed_pw)
        )
        db.commit()
        cursor.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form["email"]
    new_password = request.form["new_password"]


    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        hashed_pw = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
        db.commit()
        return "Password Updated Successfully"
    else:
        return "Email Not Found"





@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))









# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)

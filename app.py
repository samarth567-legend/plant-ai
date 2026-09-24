from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

import sqlite3
import os
import uuid
import json
from datetime import datetime

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from PIL import Image
import numpy as np
import tensorflow as tf


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "plant-ai-development-key"
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "plant_disease_mobilenetv3_final.keras"
)

CLASS_NAMES_PATH = os.path.join(
    BASE_DIR,
    "class_names.json"
)

DATABASE = os.path.join(
    BASE_DIR,
    "plant_ai.db"
)

UPLOAD_FOLDER = os.path.join(
    app.static_folder,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

IMG_SIZE = (224, 224)

UPLOAD_FOLDER = os.path.join(
    app.static_folder,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

IMG_SIZE = (224, 224)


# ============================================================
# VERIFIED CLASS ORDER
# ============================================================

DEFAULT_CLASS_NAMES = [

    "Aloe_Healthy",
    "Aloe_Rot",
    "Aloe_Rust",

    "Rose_Healthy",
    "Rose_Rust",
    "Rose_Sawfly_Slug",

    "Tulsi_Diseased",
    "Tulsi_Healthy"

]


# ============================================================
# LOAD CLASS NAMES
# ============================================================

def load_class_names():

    if os.path.exists(CLASS_NAMES_PATH):

        try:

            with open(
                CLASS_NAMES_PATH,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)


            if isinstance(data, list):

                class_names = data


            elif isinstance(data, dict):

                if all(
                    str(i) in data
                    for i in range(len(data))
                ):

                    class_names = [
                        data[str(i)]
                        for i in range(len(data))
                    ]

                elif "class_names" in data:

                    class_names = data["class_names"]

                else:

                    raise ValueError(
                        "Unknown class_names.json format."
                    )

            else:

                raise ValueError(
                    "Invalid class_names.json format."
                )


            if len(class_names) != 8:

                raise ValueError(
                    f"Expected 8 classes, found {len(class_names)}."
                )


            print()
            print("==============================================")
            print("CLASS NAMES LOADED")
            print("==============================================")

            for i, name in enumerate(class_names):

                print(
                    f"Index {i} -> {name}"
                )

            print("==============================================")
            print()


            return class_names


        except Exception as error:

            print(
                "WARNING: Could not load class_names.json"
            )

            print(error)

            print(
                "Using verified training class order."
            )


    return DEFAULT_CLASS_NAMES


CLASS_NAMES = load_class_names()


# ============================================================
# DISEASE INFORMATION
# ============================================================

DISEASE_INFO = {

    "Aloe_Healthy": {

        "plant": "Aloe Vera",

        "description":
            "The Aloe Vera leaf appears healthy.",

        "solution":
            "Continue proper watering and provide adequate sunlight."

    },


    "Aloe_Rot": {

        "plant": "Aloe Vera",

        "description":
            "The Aloe Vera leaf shows signs of rot.",

        "solution":
            "Remove affected parts and avoid excessive watering."

    },


    "Aloe_Rust": {

        "plant": "Aloe Vera",

        "description":
            "The Aloe Vera leaf shows signs of rust.",

        "solution":
            "Remove infected leaves and improve air circulation."

    },


    "Rose_Healthy": {

        "plant": "Rose",

        "description":
            "The Rose leaf appears healthy.",

        "solution":
            "Continue regular care and provide adequate sunlight."

    },


    "Rose_Rust": {

        "plant": "Rose",

        "description":
            "The Rose leaf shows signs of rust.",

        "solution":
            "Remove infected leaves and use appropriate fungicide."

    },


    "Rose_Sawfly_Slug": {

        "plant": "Rose",

        "description":
            "The Rose leaf shows signs of Sawfly/Slug damage.",

        "solution":
            "Remove affected insects and damaged leaves."

    },


    "Tulsi_Diseased": {

        "plant": "Tulsi",

        "description":
            "The Tulsi leaf shows signs of disease.",

        "solution":
            "Remove affected leaves and maintain proper plant care."

    },


    "Tulsi_Healthy": {

        "plant": "Tulsi",

        "description":
            "The Tulsi leaf appears healthy.",

        "solution":
            "Maintain proper sunlight and watering."

    }

}


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("==============================================")
print("             PLANT AI FLASK APP")
print("==============================================")

print("Model path:")
print(MODEL_PATH)

print(
    "Model exists:",
    os.path.exists(MODEL_PATH)
)


if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        "Trained model was not found. "
        "Check MODEL_PATH in app.py."
    )


print()
print("Loading MobileNetV3 model...")


model = tf.keras.models.load_model(
    MODEL_PATH
)


print("Model loaded successfully!")

print(
    "Model input shape:",
    model.input_shape
)

print(
    "Model output shape:",
    model.output_shape
)

print("==============================================")
print()


# ============================================================
# VERIFY MODEL OUTPUT
# ============================================================

try:

    output_count = int(
        model.output_shape[-1]
    )

except Exception:

    output_count = None


if output_count != len(CLASS_NAMES):

    raise RuntimeError(
        f"Model has {output_count} outputs "
        f"but CLASS_NAMES has {len(CLASS_NAMES)} classes."
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()


    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
    """)


    # --------------------------------------------------------
    # PLANTS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plants (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            plant_id TEXT UNIQUE NOT NULL,

            user_id INTEGER NOT NULL,

            plant_name TEXT NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id)
            REFERENCES users(id)

        )
    """)


    # --------------------------------------------------------
    # SCANS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            plant_id TEXT NOT NULL,

            image_path TEXT NOT NULL,

            disease TEXT NOT NULL,

            confidence REAL NOT NULL,

            health_score REAL NOT NULL,

            description TEXT,

            solution TEXT,

            scanned_at TEXT NOT NULL,

            sensor_r REAL,

            sensor_g REAL,

            sensor_b REAL,

            sensor_clear REAL,

            sensor_status TEXT,

            sensor_mode TEXT,

            FOREIGN KEY(plant_id)
            REFERENCES plants(plant_id)

        )
    """)


    # --------------------------------------------------------
    # MIGRATE OLD SCANS TABLE
    # --------------------------------------------------------

    existing_columns = [

        row["name"]

        for row in cursor.execute(
            "PRAGMA table_info(scans)"
        ).fetchall()

    ]


    sensor_columns = {

        "sensor_r": "REAL",

        "sensor_g": "REAL",

        "sensor_b": "REAL",

        "sensor_clear": "REAL",

        "sensor_status": "TEXT",

        "sensor_mode": "TEXT"

    }


    for column, column_type in sensor_columns.items():

        if column not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE scans
                ADD COLUMN {column} {column_type}
                """
            )


    # --------------------------------------------------------
    # LATEST SENSOR TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS latest_sensor (

            id INTEGER PRIMARY KEY CHECK (id = 1),

            r REAL,

            g REAL,

            b REAL,

            clear REAL,

            status TEXT,

            mode TEXT,

            updated_at TEXT

        )
    """)


    conn.commit()

    conn.close()


init_db()


# ============================================================
# SENSOR COLOR ANALYSIS
# ============================================================

def analyze_sensor_color(
    r,
    g,
    b
):

    if g > r and g > b:

        return "Green Dominant"


    elif r > g and r > b:

        return "Red/Brown Dominant"


    elif b > r and b > g:

        return "Blue Dominant"


    else:

        return "Mixed Leaf Color"


# NOTE:
# This is color dominance only.
# It does NOT independently diagnose disease.


# ============================================================
# SAVE LATEST SENSOR READING
# ============================================================

def save_latest_sensor_data(
    r,
    g,
    b,
    clear,
    status,
    mode
):

    conn = get_db()


    conn.execute("""
        INSERT INTO latest_sensor
        (
            id,
            r,
            g,
            b,
            clear,
            status,
            mode,
            updated_at
        )

        VALUES
        (
            1,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )

        ON CONFLICT(id)
        DO UPDATE SET

            r = excluded.r,

            g = excluded.g,

            b = excluded.b,

            clear = excluded.clear,

            status = excluded.status,

            mode = excluded.mode,

            updated_at = excluded.updated_at

    """, (

        r,
        g,
        b,
        clear,
        status,
        mode,

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    ))


    conn.commit()

    conn.close()


# ============================================================
# GET LATEST SENSOR READING
# ============================================================

def get_latest_sensor_data():

    conn = get_db()


    row = conn.execute("""
        SELECT
            r,
            g,
            b,
            clear,
            status,
            mode,
            updated_at

        FROM latest_sensor

        WHERE id = 1

        LIMIT 1
    """).fetchone()


    conn.close()


    if row is None:

        return None


    return {

        "r": row["r"],

        "g": row["g"],

        "b": row["b"],

        "clear": row["clear"],

        "status": row["status"],

        "mode": row["mode"],

        "updated_at": row["updated_at"]

    }


# ============================================================
# ESP32 SENSOR API
# ============================================================

@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    try:
        data = request.get_json(silent=True)

        print("\n==============================================")
        print("      TCS34725 SENSOR DATA RECEIVED")
        print("==============================================")

        if not data:
            return jsonify({"success": False, "message": "No JSON data received."}), 400

        print("Received JSON:", data)

        for field in ["r", "g", "b"]:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing sensor field: {field}"}), 400

        if "clear" in data:
            clear_value = data["clear"]
        elif "c" in data:
            clear_value = data["c"]
        else:
            return jsonify({"success": False, "message": "Missing sensor field: clear"}), 400

        r = float(data["r"])
        g = float(data["g"])
        b = float(data["b"])
        clear = float(clear_value)

        # Leaf detection: ESP32 can send explicit status; Clear < 150 is fallback.
        incoming_status = str(data.get("status", "")).strip().upper()

        if incoming_status == "NO LEAF DETECTED" or clear < 150:
            r = g = b = clear = 0.0
            status = "NO LEAF DETECTED"
            mode = "NO LEAF"
            print("\nNO LEAF DETECTED")
            print("Sensor values cleared.")
        else:
            status = analyze_sensor_color(r, g, b)
            mode = "REAL SENSOR"
            print("\nREAL SENSOR DATA SAVED")
            print("R     :", r)
            print("G     :", g)
            print("B     :", b)
            print("Clear :", clear)
            print("Status:", status)

        save_latest_sensor_data(r, g, b, clear, status, mode)

        return jsonify({
            "success": True,
            "message": "Sensor data processed successfully.",
            "r": r, "g": g, "b": b, "clear": clear,
            "status": status, "mode": mode
        }), 200

    except (ValueError, TypeError) as error:
        print("Sensor value error:", error)
        return jsonify({"success": False, "message": "Sensor values must be numeric."}), 400

    except Exception as error:
        print("Sensor API error:", error)
        return jsonify({"success": False, "message": str(error)}), 500


# ============================================================
# SENSOR ALIAS
# ============================================================

@app.route(
    "/sensor",
    methods=["POST"]
)
def sensor_alias():

    return receive_sensor_data()


# ============================================================
# LATEST SENSOR API
# ============================================================

@app.route(
    "/api/latest-sensor",
    methods=["GET"]
)
def latest_sensor_api():

    sensor = get_latest_sensor_data()


    if sensor is None:

        return jsonify({

            "success": False,

            "message":
                "No sensor data available."

        }), 404


    return jsonify({

        "success": True,

        "sensor": sensor

    })


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index (1).html"
    )


# ============================================================
# SIGNUP
# ============================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        if not name or not email or not password:

            flash(
                "Please fill all fields."
            )

            return redirect(
                url_for("signup")
            )


        hashed_password = (
            generate_password_hash(
                password
            )
        )


        conn = get_db()


        try:

            conn.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    created_at
                )

                VALUES (?, ?, ?, ?)

            """, (

                name,

                email,

                hashed_password,

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            ))


            conn.commit()

            conn.close()


            flash(
                "Account created successfully!"
            )


            return redirect(
                url_for("login")
            )


        except sqlite3.IntegrityError:

            conn.close()


            flash(
                "Email already registered."
            )


            return redirect(
                url_for("signup")
            )


    return render_template(
        "signup.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        conn = get_db()


        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?

        """, (
            email,
        )).fetchone()


        conn.close()


        if (
            user
            and
            check_password_hash(
                user["password"],
                password
            )
        ):

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]


            return redirect(
                url_for("profile")
            )


        flash(
            "Invalid email or password."
        )


    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    user_id = session["user_id"]


    conn = get_db()


    user = conn.execute("""
        SELECT
            id,
            name,
            email,
            created_at

        FROM users

        WHERE id = ?

    """, (
        user_id,
    )).fetchone()


    plants = conn.execute("""
        SELECT

            p.plant_id,

            p.plant_name,

            p.created_at,

            COUNT(s.id) AS total_scans

        FROM plants p

        LEFT JOIN scans s

        ON p.plant_id = s.plant_id

        WHERE p.user_id = ?

        GROUP BY p.plant_id

        ORDER BY p.created_at DESC

    """, (
        user_id,
    )).fetchall()


    conn.close()


    return render_template(

        "profile.html",

        user=user,

        plants=plants

    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard_home():
    """Compatibility route for templates that call url_for("dashboard") without plant_id."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    plant = conn.execute("""
        SELECT plant_id
        FROM plants
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()

    if plant:
        return redirect(url_for("dashboard", plant_id=plant["plant_id"]))

    return redirect(url_for("profile"))


@app.route(
    "/dashboard/<plant_id>"
)
def dashboard(plant_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    user_id = session["user_id"]


    conn = get_db()


    # --------------------------------------------------------
    # VERIFY PLANT
    # --------------------------------------------------------

    plant = conn.execute("""
        SELECT *

        FROM plants

        WHERE plant_id = ?

        AND user_id = ?

    """, (

        plant_id,

        user_id

    )).fetchone()


    if not plant:

        conn.close()

        return (
            "Plant not found or access denied.",
            404
        )


    # --------------------------------------------------------
    # ALL SCANS
    # --------------------------------------------------------

    scans = conn.execute("""
        SELECT *

        FROM scans

        WHERE plant_id = ?

        ORDER BY scanned_at DESC

    """, (
        plant_id,
    )).fetchall()


    latest_scan = None


    if scans:

        latest_scan = scans[0]


    total_scans = len(scans)


    # --------------------------------------------------------
    # AVERAGE HEALTH
    # --------------------------------------------------------

    average_health = 0


    if total_scans > 0:

        average_health = sum(

            float(
                scan["health_score"]
            )

            for scan in scans

        ) / total_scans


    conn.close()


    return render_template(

        "dashboard.html",

        plant=plant,

        scans=scans,

        latest_scan=latest_scan,

        total_scans=total_scans,

        average_health=round(
            average_health,
            2
        )

    )


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(filepath):

    image = Image.open(
        filepath
    ).convert("RGB")


    image = image.resize(
        IMG_SIZE,
        Image.Resampling.LANCZOS
    )


    # IMPORTANT:
    # DO NOT divide by 255.
    #
    # MobileNetV3 model already contains
    # built-in preprocessing.

    image_array = np.asarray(

        image,

        dtype=np.float32

    )


    image_array = np.expand_dims(

        image_array,

        axis=0

    )


    return image_array


# ============================================================
# AI PREDICTION
# ============================================================

def predict_image(filepath):

    image_array = preprocess_image(
        filepath
    )


    prediction = model.predict(

        image_array,

        verbose=0

    )


    probabilities = np.asarray(

        prediction[0],

        dtype=np.float32

    )


    if len(probabilities) != len(CLASS_NAMES):

        raise RuntimeError(
            "Model output count does not match class count."
        )


    total = float(
        np.sum(probabilities)
    )


    if (

        total > 0

        and

        not np.isclose(
            total,
            1.0,
            atol=0.01
        )

    ):

        probabilities = (
            probabilities / total
        )


    predicted_index = int(

        np.argmax(
            probabilities
        )

    )


    disease = CLASS_NAMES[
        predicted_index
    ]


    confidence = float(

        probabilities[
            predicted_index
        ]

        * 100.0

    )


    print()
    print("==============================================")
    print("             AI MODEL DIAGNOSIS")
    print("==============================================")


    for index, score in enumerate(
        probabilities
    ):

        print(

            f"Index {index:<2} | "
            f"{CLASS_NAMES[index]:<22} | "
            f"{float(score) * 100:>8.2f}%"

        )


    print("----------------------------------------------")

    print(
        "FINAL INDEX :",
        predicted_index
    )

    print(
        "FINAL CLASS :",
        disease
    )

    print(
        "CONFIDENCE  :",
        f"{confidence:.2f}%"
    )

    print("==============================================")
    print()


    return (

        disease,

        confidence,

        probabilities

    )


# ============================================================
# PREDICT / UPLOAD
# ============================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    # --------------------------------------------------------
    # IMAGE CHECK
    # --------------------------------------------------------

    if "image" not in request.files:

        return (
            "No image uploaded.",
            400
        )


    file = request.files[
        "image"
    ]


    if file.filename == "":

        return (
            "No image selected.",
            400
        )


    # --------------------------------------------------------
    # EXTENSION VALIDATION
    # --------------------------------------------------------

    allowed_extensions = {

        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"

    }


    original_extension = os.path.splitext(

        file.filename

    )[1].lower()


    if original_extension not in allowed_extensions:

        return (
            "Unsupported image format.",
            400
        )


    user_id = session[
        "user_id"
    ]


    # --------------------------------------------------------
    # EXISTING PLANT ID
    # --------------------------------------------------------

    plant_id = request.form.get(
        "plant_id",
        ""
    ).strip()


    conn = get_db()


    plant = None


    # --------------------------------------------------------
    # RESCAN EXISTING PLANT
    # --------------------------------------------------------

    if plant_id:

        plant = conn.execute("""
            SELECT *

            FROM plants

            WHERE plant_id = ?

            AND user_id = ?

        """, (

            plant_id,

            user_id

        )).fetchone()


        if not plant:

            conn.close()

            return (
                "Invalid plant.",
                403
            )


    # --------------------------------------------------------
    # FIRST SCAN
    # --------------------------------------------------------

    else:

        while True:

            plant_id = (

                "PLA-"

                +

                uuid.uuid4()
                .hex[:6]
                .upper()

            )


            existing = conn.execute("""
                SELECT id

                FROM plants

                WHERE plant_id = ?

            """, (
                plant_id,
            )).fetchone()


            if not existing:

                break


    # --------------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------------

    filename = (

        uuid.uuid4().hex

        +

        original_extension

    )


    filepath = os.path.join(

        UPLOAD_FOLDER,

        filename

    )


    try:

        file.save(
            filepath
        )

    except Exception as error:

        conn.close()

        return (
            f"Could not save image: {error}",
            500
        )


    # --------------------------------------------------------
    # AI PREDICTION
    # --------------------------------------------------------

    try:

        (

            disease,

            confidence,

            probabilities

        ) = predict_image(
            filepath
        )


    except Exception as error:

        conn.close()


        if os.path.exists(filepath):

            try:

                os.remove(filepath)

            except Exception:

                pass


        print(
            "AI PREDICTION ERROR:",
            error
        )


        return (
            f"AI prediction failed: {error}",
            500
        )


    # --------------------------------------------------------
    # DISEASE INFO
    # --------------------------------------------------------

    if disease not in DISEASE_INFO:

        conn.close()

        return (
            "Prediction class information not found.",
            500
        )


    info = DISEASE_INFO[
        disease
    ]


    # --------------------------------------------------------
    # HEALTH SCORE
    # --------------------------------------------------------

    if "Healthy" in disease:

        health_score = confidence

    else:

        health_score = (
            100.0 - confidence
        )


    health_score = max(

        0.0,

        min(
            100.0,
            health_score
        )

    )


    # --------------------------------------------------------
    # CREATE PLANT
    # --------------------------------------------------------

    if plant is None:

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        conn.execute("""
            INSERT INTO plants
            (
                plant_id,
                user_id,
                plant_name,
                created_at
            )

            VALUES (?, ?, ?, ?)

        """, (

            plant_id,

            user_id,

            info["plant"],

            created_at

        ))


    # --------------------------------------------------------
    # IMAGE URL
    # --------------------------------------------------------

    image_url = (

        "/static/uploads/"

        +

        filename

    )


    # --------------------------------------------------------
    # GET REAL SENSOR DATA
    # --------------------------------------------------------

    sensor = get_latest_sensor_data()


    if sensor is not None:

        sensor_r = sensor["r"]

        sensor_g = sensor["g"]

        sensor_b = sensor["b"]

        sensor_clear = sensor["clear"]

        sensor_status = sensor["status"]

        sensor_mode = sensor["mode"]


    else:

        sensor_r = None

        sensor_g = None

        sensor_b = None

        sensor_clear = None

        sensor_status = (
            "No real sensor reading available for this scan."
        )

        sensor_mode = (
            "WAITING FOR ESP32"
        )


    # --------------------------------------------------------
    # SAVE SCAN
    # --------------------------------------------------------

    scanned_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    conn.execute("""
        INSERT INTO scans
        (
            plant_id,
            image_path,
            disease,
            confidence,
            health_score,
            description,
            solution,
            scanned_at,

            sensor_r,
            sensor_g,
            sensor_b,
            sensor_clear,
            sensor_status,
            sensor_mode
        )

        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        )

    """, (

        plant_id,

        image_url,

        disease,

        confidence,

        health_score,

        info["description"],

        info["solution"],

        scanned_at,

        sensor_r,

        sensor_g,

        sensor_b,

        sensor_clear,

        sensor_status,

        sensor_mode

    ))


    conn.commit()


    # --------------------------------------------------------
    # TOTAL SCANS
    # --------------------------------------------------------

    total_scans = conn.execute("""
        SELECT COUNT(*)

        FROM scans

        WHERE plant_id = ?

    """, (
        plant_id,
    )).fetchone()[0]


    conn.close()


    # --------------------------------------------------------
    # RESULT PAGE
    # --------------------------------------------------------

    response = render_template(

        "result.html",

        plant_image=image_url,

        plant_name=info["plant"],

        disease_name=disease,

        disease=disease,

        plant_id=plant_id,

        confidence=round(
            confidence,
            2
        ),

        health_score=round(
            health_score,
            2
        ),

        total_scans=total_scans,

        description=info["description"],

        solution=info["solution"],

        sensor_r=sensor_r,

        sensor_g=sensor_g,

        sensor_b=sensor_b,

        sensor_clear=sensor_clear,

        sensor_status=sensor_status,

        sensor_mode=sensor_mode

    )

    response = app.make_response(response)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    print()
    print("==============================================")
    print("          PLANT AI SERVER STARTING")
    print("==============================================")

    print(
        "Model:",
        MODEL_PATH
    )

    print(
        "Database:",
        DATABASE
    )

    print(
        "Waiting for ESP32 sensor data..."
    )

    print("==============================================")
    print()

    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras  # ✅ This line is missing in your code
import subprocess
from twilio.rest import Client
import ast
import shutil
from urllib.parse import urlparse
from pymongo import MongoClient
import bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required ,get_jwt
from flask_jwt_extended import get_jwt_identity
from dotenv import load_dotenv
from datetime import timedelta
import random
import string
import uuid
import json


load_dotenv()
app = Flask(__name__)
CORS(app)

REPO_DIR = os.path.abspath("./git_repos")
BAT_FILE_PATH = os.path.abspath("run_python_file.bat")

os.makedirs(REPO_DIR, exist_ok=True)

db_name = os.getenv("dbname")
if db_name == "mongo":
    MONGO_URI = "mongodb://localhost:27017"  # Local MongoDB connection
    MONGO_URI = "mongodb+srv://nova:nova2346@nova.r5lap4p.mongodb.net/?retryWrites=true&w=majority&appName=nova"  # Local MongoDB connection

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # 5-second timeout
        db = client["user_database"]
        users_collection = db["users"]
        user_data_collection = db["user_data"]
        reports_collection = db["reports"]

    # Attempt to ping the database
        client.admin.command('ping')
        print("✅ Connected to local MongoDB successfully!")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        exit(1)  # Exit if DB connection fails0
elif db_name == "postgres":
    try:
        dsn = os.getenv("ostgres")
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

    # Create users table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

    # Create user_data table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        env_path TEXT[],
        report JSONB,  
        used_paths TEXT[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create reports table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        report_id UUID UNIQUE,
        email VARCHAR(255),
        title TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ PostgreSQL connected and all tables created!")
    except Exception as e:
        print(f"❌ PostgreSQL Connection or Table Creation Error: {e}")
        exit(1)

else:
    print("❌ Invalid dbname in .env. Must be either 'mongo' or 'postgres'")
    exit(1)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "Test_Execution_GUI")

jwt = JWTManager(app)
blacklist = set()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def initialize_user_data(email):
    if not user_data_collection.find_one({"email": email}):
        user_data_collection.insert_one({
            "email": email,
            "env_path": [],
            "report": [],
            "used_paths": []  
        })


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    print("Received signup data:", data)
    username = data.get("name")
    password = data.get("password")
    

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    hashed_password = hash_password(password)

    if db_name == "mongo":
        if users_collection.find_one({"name": username}):
            return jsonify({"error": "Username already exists"}), 400
        users_collection.insert_one({"name": username, "password": hashed_password})

    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = %s", (username,))
        if cur.fetchone():
            cur.close()
            return jsonify({"error": "Username already exists"}), 400
        cur.execute("INSERT INTO users (name, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cur.close()

    else:
        return jsonify({"error": "Invalid database type"}), 400

    return jsonify({"message": "User created successfully"}), 201

ADMIN_USERS = ["dass", "admin2", "superadmin","nova1"]
@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    username = data.get("name")
    password = data.get("password")

    if db_name == "mongo":
        user = users_collection.find_one({"name": username})
        if not user or not check_password(password, user["password"]):
            return jsonify({"error": "Invalid username or password"}), 401

        is_admin = username in ADMIN_USERS
        user_id = str(user["_id"])
        
        access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=1))
        
        if is_admin:
            print("Admin Login:", username)
            return jsonify({
                "access_token": access_token,
                "username": username,
                "is_admin": True
            }), 200

        return jsonify({
            "access_token": access_token,
            "username": username,
            "is_admin": False
        }), 200

    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE name = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if not user or not check_password(password, user[1]):
            return jsonify({"error": "Invalid username or password"}), 401

        user_id = str(user[0])
        access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=1))

        is_admin = username in ADMIN_USERS
        if is_admin:
            admin_token = create_access_token(identity=f"admin:{user_id}", expires_delta=timedelta(hours=2))
            return jsonify({
                "access_token": access_token,
                "admin_token": admin_token,
                "username": username,
                "is_admin": True
            }), 200

        return jsonify({
            "access_token": access_token,
            "username": username,
            "is_admin": False
        }), 200

    else:
        return jsonify({"error": "Invalid database type"}), 400

otp_storage = {}

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    username = data.get("name")
    phone = data.get("phone")

    if db_name == "mongo":
        user = users_collection.find_one({"name": username})
        if  not  user:
            return jsonify({"error": "User not found"}), 404

        otp = generate_otp()
        otp_storage[username] = otp  # Save OTP for verification


        print(f"OTP for {username}: {otp}")

        return jsonify({"message": otp}), 200
    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE name = %s", (username,))
        user = cur.fetchone()

        if not user:
                cur.close()
                conn.close()
                return jsonify({"error": "User not found"}), 404

        otp = generate_otp()
        otp_storage[username] = otp  # Save OTP for verification

        cur.close()
        conn.close()

        print(f"OTP for {username}: {otp}")
        return jsonify({"message": otp}), 200


@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    username = data.get("name")
    new_password = data.get("password")
    otp = data.get("otp")

    if db_name == "mongo":
        if not username or not new_password or not otp:
         return jsonify({"error": "All fields are required"}), 400

    # Check if user exists
        user = users_collection.find_one({"name": username})
        if not user:
            return jsonify({"error": "User not found"}), 404

    # Validate OTP
        stored_otp = otp_storage.get(username)
        if  stored_otp  != otp:
            return jsonify({"error": "Invalid OTP"}), 400

    # Hash new password and update
        hashed_password = hash_password(new_password)
        users_collection.update_one({"name": username}, {"$set": {"password": hashed_password}})

    # Remove OTP from storage after successful reset
        del otp_storage[username]

        return jsonify({"message": "Password reset successfully"}), 200
    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

            # Check if user exists
        cur.execute("SELECT * FROM users WHERE name = %s", (username,))
        user = cur.fetchone()
        if not user:
            cur.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

            # Validate OTP
        stored_otp = otp_storage.get(username)
        if stored_otp != otp:
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid OTP"}), 400

            # Hash password and update
        hashed_password = hash_password(new_password)
        cur.execute("UPDATE users SET password = %s WHERE name = %s", (hashed_password, username))

        conn.commit()
        cur.close()
        conn.close()

        del otp_storage[username]
        return jsonify({"message": "Password reset successfully"}), 200




@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]  # Get JWT unique identifier
    blacklist.add(jti)
    return jsonify({"message": "Logged out successfully"}), 200

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blacklist



def get_folder_structure(path, test_type=None):
    if not os.path.exists(path):
        return {"error": "Path does not exist"}

    # Define valid test file extensions
    valid_extensions = {
        "python": ".py",
        "java": ".java",
        "cucumber": ".feature",  # Cucumber BDD files
    }

    # Determine file extension filter
    file_extension = valid_extensions.get(test_type.lower()) if test_type else None

    def traverse(directory):
        items = []
        try:
            for entry in os.scandir(directory):
                if entry.is_dir():
                    sub_items = traverse(entry.path)
                    if sub_items or file_extension is None:  
                        items.append({
                            "name": entry.name,
                            "isfolder": True,
                            "path": entry.path,
                            "items": sub_items
                        })
                elif file_extension is None or entry.name.endswith(file_extension):  
                    items.append({
                        "name": entry.name,
                        "isfolder": False,
                        "path": entry.path
                    })
        except PermissionError:
            return []
        return items

    folder_items = traverse(path)

    if not folder_items:
        return {"error": "No matching files found"}

    return {
        "name": os.path.basename(path),
        "isfolder": True,
        "path": path,
        "items": folder_items
    }

def clone_or_update_repo(git_url):
    repo_name = os.path.basename(urlparse(git_url).path).replace(".git", "")
    repo_path = os.path.join(REPO_DIR, repo_name)

    if os.path.exists(repo_path): 
        try:
            subprocess.run(["git", "-C", repo_path, "pull"], check=True)
            return repo_path
        except subprocess.CalledProcessError:
            return None
    else:  
        try:
            subprocess.run(["git", "clone", "--depth", "1", git_url, repo_path], check=True)
            return repo_path
        except subprocess.CalledProcessError:
            shutil.rmtree(repo_path, ignore_errors=True)
            return None

'''
This route handles both GET and POST requests to fetch the folder structure.

- For GET requests:
    - Expects 'path' and 'testType' as query parameters.
- For POST requests:
    - Expects 'path' and 'testType' in the JSON body.

If the provided path is a GitHub URL, it tries to clone or update the repository.
Then, it returns the folder structure using the `get_folder_structure` function.

JWT authentication is required to access this route.
'''
@app.route("/get-folder", methods=["GET", "POST"])
@jwt_required()
def get_folder():
    path = None
    test_type = None

    if request.method == "GET":
        path = request.args.get("path")
        test_type = request.args.get("testType")
    else:
        data = request.json
        path = data.get("path")
        test_type = data.get("testType")

    if path.startswith("https://github.com/"):
        cloned_repo_path = clone_or_update_repo(path)
        if not cloned_repo_path:
            return jsonify({"error": "Failed to clone or update repository"})
        path = cloned_repo_path

    return jsonify(get_folder_structure(path, test_type))

'''
This route handles POST requests to execute a Python script in a specified virtual environment.

Expected JSON fields in the request:
- file_path: Path to the Python script to execute.
- env_path: Path to the virtual environment to use.
- testType: A string to indicate the type of test (can be passed to the script).
- arg: (Optional) List of arguments to pass to the script.

Key steps:
- Validates and normalizes the provided paths.
- Flattens the arguments list if it contains nested lists.
- Runs the script using a `.bat` file and the subprocess module.
- Captures and returns stdout, stderr, and return code.
- Optionally prints debug information and allows for saving results to MongoDB or PostgreSQL.
- JWT authentication is required to access this route.
'''
@app.route("/execute-script", methods=["POST"])
@jwt_required()
def execute_file_script():
    data = request.json
    file_path = data.get("file_path")
    env_path = data.get("env_path")
    testType = data.get("testType")
    args = data.get("arg") or []

    # Normalize env_path if it's a list
    if isinstance(env_path, list):
        env_path = env_path[0]

    # Normalize paths
    file_path = os.path.abspath(file_path)
    env_path = os.path.abspath(env_path)

    # Validate paths
    if not os.path.exists(file_path) or not file_path.endswith(".py"):
        return jsonify({"error": "Invalid file path"}), 400

    if not os.path.exists(env_path):
        return jsonify({"error": f"Invalid virtual environment path: {env_path}"}), 400

    # Flatten args safely
    if any(isinstance(arg, list) for arg in args):
        flattened_args = [item for sublist in args for item in sublist]
    else:
        flattened_args = args

    try:
        result = subprocess.run(
            [BAT_FILE_PATH, file_path, env_path, testType] + flattened_args,
            capture_output=True,
            text=True,
            shell=False  # Only keep shell=True if your .bat path needs it
        )
        print("Using DB:", db_name)
        print("File path:", file_path)
        print("Env path:", env_path)
        print("Args:", flattened_args)
        print("Command:", [BAT_FILE_PATH, file_path, env_path, testType] + flattened_args)

        # Optionally store result in Mongo/Postgres
        if db_name == "mongo":
            # You can insert the execution result into a collection if needed
            pass

        elif db_name == "postgres":
            # You can store execution logs or reports if needed here
            pass
            print("STDERR:", result.stderr)
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


'''
This route handles POST requests to validate a given Python virtual environment path.

Expected JSON field in the request:
- envPath: The path to the virtual environment.

What it does:
- Converts the given path to an absolute path.
- Checks if the path exists and contains the 'Scripts/activate.bat' file (Windows-specific).
- Returns a success message if the environment is valid.
- Returns an error message if the path is invalid or missing the activation script.

JWT authentication is required to access this route.
'''    
@app.route("/validate-env-path", methods=["POST"])
@jwt_required()
def validate_env_path():
    data = request.json
    env_path = data.get("envPath")
    
    if not env_path:
        return jsonify({"error": "envPath is required"}), 400

    env_path = os.path.abspath(env_path)
    activate_script = os.path.join(env_path, "Scripts", "activate.bat")

    if os.path.exists(env_path) and os.path.isfile(activate_script):
        return jsonify({
            "message": "Valid Python virtual environment path",
            "valid": True,
            "path": env_path
        }), 200
    else:
        return jsonify({
            "error": "Invalid environment path or missing activate.bat",
            "valid": False,
            "path": env_path
        }), 400


'''
This route handles POST requests to update the user's Python virtual environment paths.

Expected JSON field in the request:
- env_path: The new environment path to be saved.

Behavior:
- Authenticates the user using JWT and retrieves their email.
- Depending on the configured database (MongoDB or PostgreSQL), it stores the new environment path:
    - MongoDB: Adds the path to the `env_path` array in the `user_data_collection` (if not already present).
    - PostgreSQL: Adds the path to the `env_path` array column in the `user_data` table (if not already present).
- Ensures the environment path is not duplicated.
- Initializes user data if required (MongoDB).
- Returns success or error messages based on the outcome.

JWT authentication is required to access this route.
'''
@app.route("/update-env-path", methods=["POST"])
@jwt_required()
def update_env_path():
    email = get_jwt_identity()  # Get user email from token
    data = request.json
    new_env_path = data.get("env_path")
    print(new_env_path)

    if db_name == "mongo":
        if not new_env_path:
            return jsonify({"error": "env_path is required"}), 400

        initialize_user_data(email)

        user_data_collection.update_one(
            {"email": email},
            {"$addToSet": {"env_path": new_env_path}},
        )

        return jsonify({"message": "Environment path updated successfully"}), 200

    elif db_name == "postgres":
        if not new_env_path:
            return jsonify({"error": "env_path is required"}), 400

        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            cur.execute("SELECT env_path FROM user_data WHERE email = %s", (email,))
            result = cur.fetchone()

            if not result:
                cur.execute("""
                    INSERT INTO user_data (email, env_path) VALUES (%s, ARRAY[%s])
                """, (email, new_env_path))
            else:
                current_paths = result[0] or []
                if new_env_path not in current_paths:
                    cur.execute("""
                        UPDATE user_data SET env_path = array_append(env_path, %s) WHERE email = %s
                    """, (new_env_path, email))

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"message": "Environment path updated successfully"}), 200

        except Exception as e:
            return jsonify({"error": f"PostgreSQL error: {str(e)}"}), 500

# Route 2: Update Report

'''
This route handles GET requests to retrieve the list of Python virtual environment paths
saved for the authenticated user.

Behavior:
- Retrieves the user’s email from the JWT token.
- Depending on the configured database:
    - MongoDB: Queries the `user_data_collection` for the `env_path` field.
    - PostgreSQL: Queries the `user_data` table for the `env_path` array column.
- If no paths are found, returns an empty list.
- Returns the list of environment paths as a JSON response.

JWT authentication is required to access this route.
'''
@app.route("/get-env-paths", methods=["GET"])
@jwt_required()
def get_env_paths():
    email = get_jwt_identity()  # Extract user email from token
    username = request.headers.get("x-username")  # More idiomatic
    if username:
        email = get_token_without_pass(username)

    if db_name == "mongo":

        user_data = user_data_collection.find_one({"email": email}, {"env_path": 1, "_id": 0})
        if not user_data or "env_path" not in user_data:
            return jsonify({"env_paths": []})  # Return empty list if no paths exist
    
        return jsonify({"env_paths": user_data["env_path"]}), 200
    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

        cur.execute("SELECT env_path FROM user_data WHERE email = %s", (email,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if not result or result[0] is None:
            return jsonify({"env_paths": []})  # No paths exist

        return jsonify({"env_paths": result[0]}), 200  # env_path is returned as array



'''
This route handles DELETE requests to remove a specific Python virtual environment path 
associated with the authenticated user.

Expected JSON field in the request:
- env_path: The path to be removed.

Behavior:
- Extracts the user's email from the JWT token.
- Checks for the presence of the `env_path` field in the request body.
- Based on the configured database:
    - MongoDB: Uses `$pull` to remove the path from the `env_path` array in `user_data_collection`.
    - PostgreSQL: Uses `array_remove` to update the `env_path` array column in the `user_data` table.
- Returns a success message if the path is removed.
- Returns an error message if the path is not found or already removed.

JWT authentication is required to access this route.
'''
@app.route("/remove-env-path", methods=["DELETE"])
@jwt_required()
def remove_env_path():
    email = get_jwt_identity()  # Extract email from token
    data = request.get_json()
    env_path = data.get("env_path")

    if not env_path:
        return jsonify({"error": "Environment path is required"}), 400

    if db_name == "mongo":
        result = user_data_collection.update_one(
            {"email": email},
            {"$pull": {"env_path": env_path}}
        )

        if result.modified_count == 0:
            return jsonify({"error": "Path not found or already removed"}), 404

        return jsonify({"message": "Environment path removed successfully"}), 200

    elif db_name == "postgres":
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            # Pull env_path from the array using array_remove
            cur.execute("""
                UPDATE user_data
                SET env_path = array_remove(env_path, %s)
                WHERE email = %s
            """, (env_path, email))

            if cur.rowcount == 0:
                cur.close()
                conn.close()
                return jsonify({"error": "Path not found or already removed"}), 404

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"message": "Environment path removed successfully"}), 200

        except Exception as e:
            print(f"❌ PostgreSQL error in remove_env_path: {e}")
            return jsonify({"error": "Failed to remove path"}), 500

    else:
        return jsonify({"error": "Invalid database type"}), 400

'''
This route handles POST requests to update a report for the authenticated user.

Expected JSON fields in the request:
- report_id: The ID of the report to be updated.
- name: The name of the report.

Behavior:
- Extracts the user's email from the JWT token.
- Checks that both the `report_id` and `name` are provided in the request.
- Based on the configured database:
    - MongoDB: Uses `$addToSet` to add the report ID and name to the `report` field of the user's document in the `user_data_collection`.
    - PostgreSQL: Fetches the current list of reports, adds the new report entry (if not already present), and performs an upsert operation to update the reports.
- Returns a success message if the report is updated successfully.
- Returns an error message if required fields are missing or there is an issue with the database.

JWT authentication is required to access this route.
'''
@app.route("/update-report", methods=["POST"])
@jwt_required()
def update_report():
    email = get_jwt_identity()
    data = request.json
    new_report = data.get("report_id")
    name = data.get("name")
    print("ID",new_report)

    if not new_report or not name:
        return jsonify({"error": "Both name and report_id are required"}), 400

    if db_name == "mongo":
        initialize_user_data(email)
        user_data_collection.update_one(
            {"email": email},
            {"$addToSet": {"report": [name, new_report]}}
        )
        return jsonify({"message": "Report updated successfully"}), 200

    elif db_name == "postgres":
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            cur.execute("SELECT report FROM user_data WHERE email = %s", (email,))
            result = cur.fetchone()

            new_entry = {"name": name, "report_id": new_report}
            print(new_entry)

            current_report = []
            if result and result[0]:
                try:
                    current_report = result[0] if isinstance(result[0], list) else []
                except Exception as e:
                    print("⚠️ Error loading existing report JSON:", e)

        # Only add if not already present
            if new_entry not in current_report:
                current_report.append(new_entry)

        # Upsert logic
            cur.execute("""
            INSERT INTO user_data (email, report)
            VALUES (%s, %s)
            ON CONFLICT (email) 
            DO UPDATE SET report = %s
         """, (email, json.dumps(current_report),json.dumps(current_report)
))

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"message": "Report updated successfully"}), 200

        except Exception as e:
            print(f"❌ PostgreSQL Error updating report: {e}")
            return jsonify({"error": str(e)}), 500


'''
This route handles POST requests to create a new script, store its content, 
and save metadata in the database.

Expected JSON fields in the request:
- name: The name of the script.
- script: The actual content of the script.

Behavior:
- Extracts the user's ID from the JWT token.
- Validates that both the script name and content are provided.
- Generates a unique report ID using UUID.
- Based on the configured database:
    - MongoDB: Creates a new document in the `reports_collection` with the script's metadata (`name`, `script_content`, `user_id`).
    - PostgreSQL: Inserts the script data into the `reports` table.
- Returns a success message with the report ID after the script is successfully stored.
- Returns an error message if required fields are missing or if there is an issue with the database.

JWT authentication is required to access this route.
'''
@app.route("/create-script", methods=["POST"])
@jwt_required()
def create_script():
    """
    Create a .txt file, store the script content, and save metadata in DB.
    """
    user_id = get_jwt_identity()
    data = request.json
    print(user_id)
    print(data)

    name = data.get("name")
    script_content = data.get("script")

    if not name or not script_content:
        return jsonify({"error": "Name and script content are required"}), 400

    report_id = str(uuid.uuid4())  # can still generate a UUID even for Postgres usage

    if db_name == "mongo":
        report_data = {
        "_id": report_id,  # ✅ save as report_id
        "user_id": user_id,
        "file_name": name,
        "file_data": script_content,
        }
        
        reports_collection.insert_one(report_data)
        return jsonify({"message": "Script stored successfully", "report_id": report_id}), 201

    elif db_name == "postgres":
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            # Insert into PostgreSQL reports table
            cur.execute("""
                INSERT INTO reports (report_id,email, title, content)
                VALUES (%s, %s, %s,%s)
                
            """, (report_id,user_id, name, script_content))

            # report_id = cur.fetchone()[0]

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"message": "Script stored successfully", "report_id": report_id}), 201

        except Exception as e:
            print(f"❌ PostgreSQL error in create_script: {e}")
            return jsonify({"error": "Failed to store script"}), 500

    else:
        return jsonify({"error": "Invalid database type"}), 400

'''
This route handles GET requests to retrieve a script based on the provided report ID.

Expected URL parameter:
- report_id: The unique identifier for the script.

Behavior:
- Extracts the user's ID from the JWT token.
- Based on the configured database:
    - MongoDB: Searches for a document in `reports_collection` matching the report ID and user ID, returning the script content if found.
    - PostgreSQL: Retrieves the script name and content from the `reports` table based on the report ID and user ID.
- Returns the script's content and report ID if found.
- Returns an error message if the report is not found or if there's a database issue.

JWT authentication is required to access this route.
'''    
@app.route("/get-script/<report_id>", methods=["GET"])
@jwt_required()
def get_script(report_id):
    """
    Retrieve the script content using the report ID.
    Works for both MongoDB and PostgreSQL.
    """
    user_id = get_jwt_identity()  # Could be email or user_id depending on your token

    if db_name == "mongo":
        report = reports_collection.find_one({"_id": report_id, "user_id": user_id})

        if not report:
            return jsonify({"error": "Report not found"}), 404

        return jsonify({
            "report_id": report_id,
            "file_content": report["file_data"]
        }), 200

    elif db_name == "postgres":
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            cur.execute(
                "SELECT title, content FROM reports WHERE report_id = %s AND email = %s",
                (report_id, user_id)
            )
            result = cur.fetchone()

            cur.close()
            conn.close()

            if not result:
                return jsonify({"error": "Report not found"}), 404

            return jsonify({
                "report_id": report_id,
                "name": result[0],
                "file_content": result[1]
            }), 200

        except Exception as e:
            print(f"❌ PostgreSQL Error retrieving script: {e}")
            return jsonify({"error": "Database error"}), 500

    else:
        return jsonify({"error": "Invalid database type"}), 400




from bson import ObjectId

def get_username_from_id(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user["name"] if user else None
    except Exception as e:
        print(f"❌ Error in get_username_from_id: {e}")
        return None


'''
This route handles GET requests to fetch all reports for a user based on their email (or user ID) extracted from the JWT token.

Expected behavior:
- Extracts the user's email or ID from the JWT token.
- Based on the configured database:
    - MongoDB: Retrieves all reports associated with the user's email from the `reports_collection`.
    - PostgreSQL: Queries the `reports` table for reports associated with the user's email, including report ID, title, content, and creation timestamp.
- The function converts any MongoDB ObjectId to a string before returning the reports.
- In PostgreSQL, the creation timestamp is formatted in ISO 8601 format.
- Returns a list of reports for the user or an error message if something goes wrong.
'''

@app.route("/get-user-reports", methods=["GET"])
@jwt_required()
def get_user_reports():
    user_id = get_jwt_identity()
    requester_username = get_username_from_id(user_id)
    is_admin = requester_username in ADMIN_USERS

    # Optional: query param to fetch reports for specific user (admin only)
    target_username = request.args.get("username")

    if db_name == "mongo":
        if is_admin and target_username:
            target_user = users_collection.find_one({"name": target_username})
            if not target_user:
                return jsonify({"error": "Target user not found"}), 404
            target_user_id = str(target_user["_id"])
            user_reports = list(reports_collection.find({"user_id": target_user_id}))
        else:
            # Normal user or admin without target => get own reports
            user_reports = list(reports_collection.find({"user_id": user_id}))

        for report in user_reports:
            report["_id"] = str(report["_id"])  # ObjectId to string

        return jsonify({"reports": user_reports}), 200

    elif db_name == "postgres":
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            if is_admin and target_username:
                cur.execute("SELECT email FROM users WHERE name = %s", (target_username,))
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Target user not found"}), 404
                target_email = row[0]

                cur.execute("""
                    SELECT report_id, email, title, content, created_at
                    FROM reports
                    WHERE email = %s
                """, (target_email,))
            else:
                cur.execute("""
                    SELECT report_id, email, title, content, created_at
                    FROM reports
                    WHERE email = %s
                """, (user_id,))

            rows = cur.fetchall()
            cur.close()
            conn.close()

            reports = [
                {
                    "report_id": row[0],
                    "email": row[1],
                    "file_name": row[2],
                    "file_data": row[3],
                    "created_at": row[4].isoformat() if row[4] else None 
                }
                for row in rows
            ]

            return jsonify({"reports": reports}), 200

        except Exception as e:
            print(f"❌ Error fetching reports from PostgreSQL: {e}")
            return jsonify({"error": "Failed to fetch reports"}), 500

    else:
        return jsonify({"error": "Invalid database type"}), 400

@app.route("/delete-report/<report_id>", methods=["DELETE"])
@jwt_required()
def delete_report(report_id):
    current_user_id = get_jwt_identity()
    username = get_username_from_id(current_user_id)
    is_admin = username in ADMIN_USERS

    if not is_admin:
        return jsonify({"error": "Not authorized"}), 403

    if db_name == "mongo":
        result = reports_collection.delete_one({"_id": report_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Report not found"}), 404
        print("repot not found")
        return jsonify({"message": "Report deleted"}), 200

    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute("DELETE FROM reports WHERE report_id = %s", (report_id,))
        conn.commit()
        cur.close()
        return jsonify({"message": "Report deleted"}), 200


def extract_options(file_path):
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    options = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr == "addoption":
            # Handle both Python versions (pre-3.8 and post-3.8)
            args = [arg.value if isinstance(arg, ast.Constant) else arg.s for arg in node.args if isinstance(arg, (ast.Str, ast.Constant))]
            kwargs = {kw.arg: (kw.value.value if isinstance(kw.value, ast.Constant) else kw.value.s) 
                      for kw in node.keywords if isinstance(kw.value, (ast.Str, ast.Constant))}
            
            options.append([
                args[0] if args else "",
                f"action={kwargs.get('action', '')}",
                f"type={kwargs.get('type', '')}",
                f"help={kwargs.get('help', '')}"
            ])
    return options

'''
This route handles POST requests to check arguments in a specified file.

Expected behavior:
- The route receives a JSON payload containing a "path" parameter, which is expected to be the file path.
- If the "path" parameter is missing, it returns an error response with status code 400.
- If the "path" parameter is provided, it tries to extract options from the file located at the given path using the `extract_options` function.
- If the extraction is successful, the response is returned as JSON.
- If any error occurs during the extraction, it logs the error and returns a 500 error response with the error message.

This route is typically used for processing files and extracting specific options from them based on the provided file path.
'''
@app.route("/chech_arg", methods=["POST"])
def check_arg():
    data = request.get_json()
    file_path = data.get("path")

    if not file_path:
        return jsonify({"error": "Missing path parameter"}), 400
    print(file_path)
    try:
        response = extract_options(file_path)
        return jsonify(response)
    except Exception as e:
        print(f"Error processing file: {str(e)}")  # Log error
        return jsonify({"error": str(e)}), 500

'''
This route handles storing a used path for a specific user.

Expected behavior:
- The route receives a POST request containing a "used_path" parameter in the JSON body.
- If the "used_path" parameter is missing, it returns an error response with status code 400.
- If the "used_path" is provided:
  - In MongoDB: It initializes the user's data and adds the path to the "used_paths" array, ensuring no duplicates with the `$addToSet` operator.
  - In PostgreSQL: It checks if the user already has a "used_paths" array. 
  If so, it adds the new path to the array. If the user doesn't have "used_paths" stored yet, it creates a new record and stores the path in an array.
- If any error occurs during the database operations, a 500 error is returned with an error message.

This route is typically used to track the paths that a user has already used in the application, preventing redundant processing of the same paths.
'''
@app.route("/store-used-path", methods=["POST"])
@jwt_required()
def store_used_path():
    email = get_jwt_identity()
    data = request.get_json()
    used_path = data.get("used_path")

    if not used_path:
        return jsonify({"error": "used_path is required"}), 400

    if db_name == "mongo":
        initialize_user_data(email)

        user_data_collection.update_one(
            {"email": email},
            {"$addToSet": {"used_paths": used_path}}  # addToSet prevents duplicates
        )

        return jsonify({"message": "Used path stored successfully"}), 200

    elif db_name == "postgres":
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()

            # Check if user_data exists
            cur.execute("SELECT used_paths FROM user_data WHERE email = %s", (email,))
            result = cur.fetchone()

            if result:
                current_paths = result[0] or []
                if used_path not in current_paths:
                     cur.execute("""
                    UPDATE user_data 
                    SET used_paths = array_append(used_paths, %s) 
                    WHERE email = %s
                """, (used_path, email))
            else:
                cur.execute("""
                    INSERT INTO user_data (email, used_paths)
                    VALUES (%s, ARRAY[%s])
                """, (email, used_path))

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"message": "Used path stored successfully"}), 200

        except Exception as e:
            print(f"❌ PostgreSQL Error storing used path: {e}")
            return jsonify({"error": "Database error"}), 500

    else:
        return jsonify({"error": "Invalid database type"}), 400


'''
This route handles retrieving the list of "used_paths" associated with the authenticated user.

Expected behavior:
- The route receives a GET request and expects a valid JWT token for user authentication.
- The "email" or "user_id" of the authenticated user is extracted from the JWT token.
- The response contains a list of paths the user has already used, either from MongoDB or PostgreSQL.

Database Handling:
- In MongoDB:
    - The function queries the "user_data_collection" for the document that matches the user's email.
    - It checks if the "used_paths" field exists, and returns the list of paths if found.
    - If no paths are found, it returns an empty list.
  
- In PostgreSQL:
    - The function queries the "user_data" table to retrieve the "used_paths" array for the given email.
    - If no paths are found, it returns an empty list.
  
- In either case, a successful response returns the list of used paths in a JSON object.

If there is an issue with the database or the user data, the function will return an empty list.
'''
@app.route("/get-used-paths", methods=["GET"])
@jwt_required()
def get_used_paths():
    email = get_jwt_identity()
    
    if db_name == "mongo":
         
        user_data = user_data_collection.find_one({"email": email}, {"used_paths": 1, "_id": 0})
    
        if not user_data or "used_paths" not in user_data:
            return jsonify({"used_paths": []}), 200

        return jsonify({"used_paths": user_data["used_paths"]}), 200
    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

        cur.execute("SELECT used_paths FROM user_data WHERE email = %s", (email,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if not result or result[0] is None:
            return jsonify({"used_paths": []}), 200

        return jsonify({"used_paths": result[0]}), 200 

@app.route("/api/users")
@jwt_required()
def get_all_users():
    if db_name == "mongo":
        users = users_collection.distinct("name")
    elif db_name == "postgres":
        cur = conn.cursor()
        cur.execute("SELECT name FROM users")
        users = [row[0] for row in cur.fetchall()]
        cur.close()
    return jsonify({"users": users})


def get_token_without_pass(username):
    """
    Returns a JWT access token for the given username without checking password.
    Only use in secure/admin context.
    """
    # Look up the user to verify existence (optional but recommended)
    user_id = None
    if db_name == "mongo":
        user = users_collection.find_one({"name": username})
        if not user:
            return jsonify({"error": "User not found"}), 404
        user_id = str(user["_id"])

    elif db_name == "postgres":
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE name = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({"error": "User not found"}), 404
        user_id = str(row[0])

    else:
        return jsonify({"error": "Invalid database type"}), 400

    return user_id


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

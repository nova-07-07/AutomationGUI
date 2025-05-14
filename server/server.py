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
        dsn = "postgres://avnadmin:AVNS_6gDCKyGCc5GFq0opToJ@pg-4d01fba-rajp18733-1d7a.h.aivencloud.com:22599/defaultdb?sslmode=require"
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

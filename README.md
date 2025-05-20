# 🧪 AutomationGUI


---

## 🚀 Installation & Setup

Follow these steps to run the project locally.

---

### 1. Clone the Repository

git clone https://github.com/nova-07-07/AutomationGUI
cd AutomationGUI


### 2.Install Backend Dependencies
    cd server 
    pip install -r requirements.txt

### 3.Create a .env put values to runs the server
    dbname = your_database_name              #example:(mongo (or) postgres )
    JWT_SECRET_KEY = secret_key              #(your secret key)
    mongoDbDns = mongodb+srv://mongUser:.... #(your mongoDb Dns)
    PostgresDns = postgres://avnadmin:...... #(your postgres Dns)


### 4.Run the Backend Server
    cd server 
    python server.py

### 5.Install Frontend Dependencies
    cd client npm install

### 6.Run the Frontend
    cd client 
    npm run dev

### 7.Open the browser and put the url something like http://localhost:5173/

***thanks for using our application!***
import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./AddUser.css";


function AddUser() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("user");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleAddUser = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await axios.post(
        "http://localhost:5000/signup",
        { name, password, role },
        { headers: { "Content-Type": "application/json" } }
      );

      // Redirect on success
      navigate("/Admin_Edit_page");
    } catch (error) {
      if (error.response?.status === 400) {
        setError("User already exists.");
      } else {
        setError("Failed to add user. Please try again.");
      }
    }
  };

  return (
    <div className="add-user-page">
      <div style={{backgroundColor:"#f2f2f2"}}><button className="ad-ed-back bg-black" onClick={() => window.location.href = "/Admin_Edit_page"}>Back</button></div>
      
    <div className="add-user-container" >
      
      <h2>Add New User</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
        <div className="add-user-form-container">
      <form onSubmit={handleAddUser}>
        <input
          type="text"
          placeholder="Username"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
        >
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>

        <button type="submit">Add User</button>
      </form>
      </div>
    </div>
    </div>
  );
}

export default AddUser;

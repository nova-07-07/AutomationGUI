import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Admin_Edit_page.css";

function Admin_Edit_page() {
  const [username, setUsername] = useState("");
  const [adminUsers, setAdminUsers] = useState([]);
  const [nonAdminUsers, setNonAdminUsers] = useState([]);
  const [selectedUserisAdmin, setSelectedUserisAdmin] = useState(false);

  const token = localStorage.getItem("token");
  const accessAdmin = localStorage.getItem("username");
  const logdinAdmin = localStorage.getItem("username");

  useEffect(() => {
    if (localStorage.getItem("is_admin") !== "true") {
      alert("Unauthorized access! Please log in again.");
      window.location.href = "/signin";
      return;
    }

    const fetchData = async () => {
      try {
        const [usersRes] = await Promise.all([
          axios.get("http://localhost:5000/api/users", {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        const allUsers = usersRes.data.users;   
        console.log(allUsers);
        
        const nonAdmins = allUsers.filter(user => user.role !== "admin"); // Exclude admin users
        const admins = allUsers.filter(user => user.role === "admin"); // Get admin users
        
        setAdminUsers(admins);
        setNonAdminUsers(nonAdmins);

      } catch (err) {
        console.error("Error fetching data:", err.response?.data?.error || err.message);
        alert(err.response?.data?.error || "Unable to fetch user data.");
      }
    };

    fetchData();
  }, [token, logdinAdmin]);

  const addAdmin = async (username) => {
    try {
      const response = await axios.post(
        "http://localhost:5000/addAdminUsers",
        { accessAdmin, username },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(response.data.message);
      window.location.reload();
    } catch (err) {
      console.error("Error adding admin:", err.response?.data?.error || err.message);
      alert(err.response?.data?.error || "Failed to add admin");
    }
  };

  const removeAdmin = async (username) => {
    if (username === logdinAdmin) {
      alert("You cannot remove yourself as admin.");
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:5000/removeAdminUsers",
        { accessAdmin, username },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(response.data.message);
      window.location.reload();
    } catch (err) {
      console.error("Error removing admin:", err.response?.data?.error || err.message);
      alert(err.response?.data?.error || "Failed to remove admin");
    }
  };

  return (
    <div className="ad-ed-admin-container-t">
      <div className="ad-ed-admin-content">
        <div className="ad-ed-admin-header">
        <button className="ad-ed-back" onClick={() => window.location.href = "/Admin_Page"}>Back</button>
        <button className="ad-ed-back" onClick={() => window.location.href = "/Add_User_Page"}>Add User</button>
        </div>
        
        <h2 className="ad-ed-admin-title">Admin Management</h2>

        <input
          type="text"
          className="ad-ed-admin-input"
          placeholder="Enter username or click on user from list"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <div className="ad-ed-admin-button-group">
          <button
            className="ad-ed-admin-button ad-ed-add"
            onClick={() => addAdmin(username)}
            disabled={!username || selectedUserisAdmin}
          >
            Add Admin
          </button>
          <button
            className="ad-ed-admin-button ad-ed-remove"
            onClick={() => removeAdmin(username)}
            disabled={!username || !selectedUserisAdmin}
          >
            Remove Admin
          </button>
        </div>

        <div className="ad-ed-user-list-container">
          <div className="ad-ed-user-list">
            <div className="ad-ed-admin-list">
              <h3 className="ad-ed-admin-list-title">Admin Users</h3>
              {adminUsers.length === 0 ? (
                <p>No admin users found (excluding yourself).</p>
              ) : (
                <ul>
                  {adminUsers.map((name, index) => (
                    <li key={index} onClick={() => { setUsername(name.name); setSelectedUserisAdmin(true); }}>
                      <span className="ad-ed-user-name">{name.name}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="ad-ed-users-list">
            <h3>Non-Admin Users </h3>
            {nonAdminUsers.length === 0 ? (
              <p>No non-admin users found.</p>
            ) : (
              <ul>
                {nonAdminUsers.map((user, index) => (
                  <li key={index} onClick={() => { setUsername(user.name); setSelectedUserisAdmin(false); }}>
                    <span className="ad-ed-user-name">
                      {user.name} 
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Admin_Edit_page;

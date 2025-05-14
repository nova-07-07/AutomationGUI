import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./Admin_Edit_page.css";

function Admin_Edit_page() {
  const [username, setUsername] = useState("");
  const [adminUsers, setAdminUsers] = useState([]);
  const [nonAdminUsers, setNonAdminUsers] = useState([]);

  const token = localStorage.getItem("token");
  const accessAdmin = localStorage.getItem("username");

  const fetchAdminUsers = useCallback(async () => {
    try {
      const response = await axios.get("http://localhost:5000/getAdminUsers", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAdminUsers(response.data.admin_users);
    } catch (err) {
      console.error("Failed to fetch admin users:", err.response?.data?.error || err.message);
      alert(err.response?.data?.error || "Unable to fetch admin list.");
    }
  }, [token]);

  const fetchUsers = useCallback(async () => {
    try {
      const response = await axios.get("http://localhost:5000/api/users", {
        headers: { Authorization: `Bearer ${token}` },
      });

      const filteredUsers = response.data.users.filter(user => !adminUsers.includes(user));
      setNonAdminUsers(filteredUsers);
    } catch (err) {
      console.error("Failed to fetch users:", err.response?.data?.error || err.message);
      alert(err.response?.data?.error || "Unable to fetch users.");
    }
  }, [token, adminUsers]);

  useEffect(() => {
    if (localStorage.getItem("is_admin") !== "true") {
      alert("Unauthorized access! Please log in again.");
      window.location.href = "/signin";
      return;
    }

    (async () => {
      await fetchAdminUsers();
    })();
  }, [fetchAdminUsers]);

  // Refetch non-admin users whenever adminUsers changes
  useEffect(() => {
    if (adminUsers.length) {
      fetchUsers();
    }
  }, [adminUsers, fetchUsers]);

  const addAdmin = async (username) => {
    try {
      const response = await axios.post(
        "http://localhost:5000/addAdminUsers",
        { accessAdmin, username },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(response.data.message);
      await fetchAdminUsers();
    } catch (err) {
      console.error("Error adding admin:", err.response?.data?.error || err.message);
      alert(err.response?.data?.error || "Failed to add admin");
    }
  };

  const removeAdmin = async (username) => {
    try {
      const response = await axios.post(
        "http://localhost:5000/removeAdminUsers",
        { accessAdmin, username },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(response.data.message);
      await fetchAdminUsers();
    } catch (err) {
      console.error("Error removing admin:", err.response?.data?.error || err.message);
      alert(err.response?.data?.error || "Failed to remove admin");
    }
  };

  return (
    <div className="ad-ed-admin-container-t">
        <div className="ad-ed-admin-content">
            <button className="ad-ed-back" onClick={()=> window.location.href = "/Admin_Page"}>Back</button>
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
      disabled={!username}
    >
      Add Admin
    </button>
    <button
      className="ad-ed-admin-button ad-ed-remove"
      onClick={() => removeAdmin(username)}
      disabled={!username}
    >
      Remove Admin
    </button>
  </div>

  <div className="ad-ed-user-list">
    <div className="ad-ed-admin-list">
      <h3>Current Admin Users</h3>
      <ul>
        {adminUsers.map((user, index) => (
          <li key={index} onClick={() => setUsername(user)}>
            <span className="ad-ed-user-name">{user}</span>
          </li>
        ))}
      </ul>
    </div>

    <div className="ad-ed-users-list">
      <h3>All Users (excluding admins)</h3>
      <ul>
        {nonAdminUsers.map((user, index) => (
          <li key={index} onClick={() => setUsername(user)}>
            <span className="ad-ed-user-name">{user}</span>
          </li>
        ))}
      </ul>
    </div>
  </div>

        </div>
  </div>

  );
}

export default Admin_Edit_page;

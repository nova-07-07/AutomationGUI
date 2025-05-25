import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Admin_Page.css';

const Admin_Page = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userReports, setUserReports] = useState([]);
  const [userEnvPaths, setUserEnvPaths] = useState([]);
  const [showEnvPaths, setShowEnvPaths] = useState(false);
  const [openReports, setOpenReports] = useState({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem("token");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get("http://localhost:5000/api/users", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsers(response.data.users || []);
      } catch (err) {
        console.error(err);
        setError('Failed to load users.');
      }
    };

    fetchUsers();
  }, [token]);

  const handleUserClick = async (username) => {
    setSelectedUser(username);
    setShowEnvPaths(false);
    setUserReports([]);
    setUserEnvPaths([]);
    setError('');
    setLoading(true);
    setOpenReports({});

    try {
      const response = await axios.get(`http://localhost:5000/get-user-reports?username=${username}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUserReports(response.data.reports || []);
    } catch (err) {
      console.error(err);
      setError('Failed to load user reports.');
    } finally {
      setLoading(false);
    }
  };

  const fetchEnvPaths = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.get("http://localhost:5000/get-env-paths", {
        headers: {
          Authorization: `Bearer ${token}`,
          "x-username": selectedUser,
          "Content-Type": "application/json",
        },
      });

      setUserEnvPaths(response.data.env_paths || []);
      setShowEnvPaths(true);
    } catch (err) {
      console.error("Failed to fetch env paths:", err);
      setError('Failed to load environment paths.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (id) => {
    setOpenReports((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleDelete = async (id, event) => {
    event.stopPropagation(); // Prevent toggle on delete
    try {
      const response = await axios.delete(`http://localhost:5000/delete-report/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 200) {
        setUserReports((prev) =>
          prev.filter((item) => item._id !== id && item.report_id !== id)
        );
        alert("Report deleted successfully.");
      } else {
        alert("Error deleting report.");
      }
    } catch (err) {
      console.error("Error deleting report:", err);
      alert("Error deleting report.");
    }
  };

  return (
    <div className="admin-container">
      <div className="AdminNav">
        <h2>Admin Panel</h2>
        <div className="AdminNav-buttons">
          <button className="navigate-button" onClick={() => navigate('/ExecutePage')}>Execute Page</button>
          <button className="navigate-button" onClick={() => navigate('/home_page')}>Home Page</button>
          <button className="navigate-button" onClick={() => navigate('/Admin_Edit_page')}>Admin Edit Page</button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="grid-container">
        <div className="card">
          <h2>Users</h2>
          <ul className="user-list">
            {users.map((user, index) => (
              <li key={user.name || index} onClick={() => handleUserClick(user.name)}>
                {user.name} ({user.role})
              </li>
            ))}
          </ul>
        </div>

        {selectedUser && (
          <div className="cardRight">
            <div className="cardRight-nav">
              <h3>
                <b>
                  {selectedUser.charAt(0).toUpperCase() + selectedUser.slice(1)}{' '}
                  {showEnvPaths ? 'Env Paths' : 'Reports'}
                </b>
              </h3>
              <button
                className="changerBtn"
                onClick={() => {
                  if (showEnvPaths) {
                    setShowEnvPaths(false);
                  } else {
                    fetchEnvPaths();
                  }
                }}
              >
                {showEnvPaths ? 'Show Reports' : 'Env Paths'}
              </button>
            </div>

            {loading ? (
              <div className="spinner"></div>
            ) : showEnvPaths ? (
              <ul className="report-list">
                {userEnvPaths.length > 0 ? (
                  userEnvPaths.map((path, idx) => (
                    <li key={idx} className="report-item">
                      <b>{path.split("\\").pop()}</b> : {path}
                    </li>
                  ))
                ) : (
                  <p>No environment paths available.</p>
                )}
              </ul>
            ) : (
              <ul className="report-list">
                {userReports.length > 0 ? (
                  userReports.map((report) => {
                    const reportId = report._id || report.report_id || Math.random().toString(36).substring(2);
                    const isOpen = openReports[reportId];
                    return (
                      <li key={reportId} className="report-item">
                        <div
                          className="report-title"
                          onClick={() => handleToggle(reportId)}
                          style={{ cursor: 'pointer', fontWeight: 'bold' }}
                        >
                          {report.file_name || report.title || "Unnamed Report"}
                          <button
                            className="delete-button"
                            onClick={(e) => handleDelete(reportId, e)}
                          >
                            Delete
                          </button>
                        </div>
                        {isOpen && (
                          <pre className="report-content">
                            {report.file_data || report.content || "No content"}
                          </pre>
                        )}
                      </li>
                    );
                  })
                ) : (
                  <p>No reports available.</p>
                )}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin_Page;

import { useEffect, useState } from "react";
import "./SettingsMenu.css";
import { useNavigate } from "react-router-dom";
import { FaUserCircle } from "react-icons/fa";

export default function SettingsMenu({ setGetEnv,settingExit, SetShowReportSave, SetShowReportShow, setDisplayBlack, setTestType ,setDisSet , setSettingExit}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [testSettingsOpen, setTestSettingsOpen] = useState(false);
  const [reportsOpen, setReportsOpen] = useState(false);
  const [testType, setTestTypeVar] = useState("python");
  const[Username, setusername ] = useState("praveen")
  
  useEffect(()=>{
    setDisSet(menuOpen);
  },[menuOpen])

  useEffect(()=>{
    setMenuOpen(false);
    setTestSettingsOpen(false);
  },[settingExit])
  
  const navigate = useNavigate();
  
  const handleLogout = async () => {
    try {
      const response = await fetch("http://localhost:5000/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      
      if (response.ok) {
        localStorage.removeItem("token"); 
        localStorage.removeItem("username");
      } 
      navigate("/");
    } catch (error) {
      alert("Network error, please try again.");
    }
  };

  return (
    <div className="settings-container">
      {/* Buttons to open Reports or Settings */}
      <div className="bbt">
        <button 
          className="settings-button report-button" 
          onClick={() => { 
            setReportsOpen(!reportsOpen);
            setTestSettingsOpen(false);
            setMenuOpen(false);
            setSettingExit(true);
          }}
          title="Reports"
        >
          📝
        </button>
        <button 
          className="settings-button" 
          onClick={() => { 
            setReportsOpen(false);
            setTestSettingsOpen(false);
            setMenuOpen(!menuOpen);
            setSettingExit(true);
          }}
          title="Settings"
        >
          ⚙️
        </button>
      </div>

      {/* Settings Menu */}
      {menuOpen && !testSettingsOpen && !reportsOpen && (
        <div className="menu-container">
          <ul>
            <li>
            
            <FaUserCircle size={25} className="userlogo" /><span className="name">{localStorage.getItem("username")}</span>

            </li>
            <li>
              <button className="btn_select" onClick={handleLogout}>
                Logout
              </button>
            </li>
            <li>
              <button className="btn_select" onClick={() => setTestSettingsOpen(true)}>
                Test Settings
              </button>
            </li>
          </ul>
        </div>
      )}

      {/* Test Settings */}
      {testSettingsOpen && (
        <div className="left-nav-con">
          <div className="test-settings-container">
            <button className="back-button" onClick={() => setTestSettingsOpen(false)}>← Back</button>
            <button className="btn_select" onClick={() => { 
                setGetEnv(true);
                setMenuOpen(false);
                setDisplayBlack(true);
                setTestSettingsOpen(false);
            }}>
              Environment
            </button>
            <div>
              <label className="test_type_lab">Test Type</label>
              <select className="dropdown" value={testType} onChange={(e) => {
                setTestType(e.target.value);
                setTestTypeVar(e.target.value);
              }}>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="cucumber">Cucumber</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {reportsOpen && (
        <div className="left-nav-con">
          <div className="test-settings-container">
            <button className="btn_select" onClick={() => { 
                SetShowReportSave(true);
                setMenuOpen(false);
                setReportsOpen(false);
                setDisplayBlack(true);
            }}>
              Save Reports
            </button>
            <button className="btn_select" onClick={() => { 
                SetShowReportShow(true);
                setMenuOpen(false);
                setReportsOpen(false);
                setDisplayBlack(true);
            }}>
              Show Reports
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

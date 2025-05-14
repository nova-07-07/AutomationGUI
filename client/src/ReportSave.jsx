import { useState } from "react";
import { useNavigate } from "react-router-dom";

const ReportSave = ({SetShowReportSave, output , backgroundSelect}) => {
  const [name, setName] = useState("");
  const [savedReportId, setSavedReportId] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSave = async () => {
    const tt = localStorage.getItem("token");
    if (!tt) {
      alert("something is wrong please login again");
      navigate("/signin")
    }
  

    if (!name || !output) {
      setError("Name and output are required!");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      let response = await fetch("http://localhost:5000/create-script", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // Send token for authentication
        },
        body: JSON.stringify({
          name,
          script: output,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setSavedReportId(data.report_id);
        setError(null);
        //SetShowReportSave(false);
      } else {
        setError(data.error || "Failed to save the report");
      }
        response = await fetch("http://localhost:5000/update-report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, 
        },
        body: JSON.stringify({
          report_id: savedReportId,
          name
        }),
      });
      
      alert("report saved");
      SetShowReportSave(false);
      backgroundSelect();
    } catch (err) {
      setError("Error saving report: " + err.message);
      alert("Error saving report: " + err.message);
      SetShowReportSave(false);
      backgroundSelect();
      alert("something is wrong please login again");
      navigator("/signin")
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: "35%",
        left: "35%",
        right: "35%",
        bottom: "35%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        maxWidth: "max-conten",
        maxHeight: "max-conten",
        color: "black",
        pointerEvents: "auto",
        backgroundColor: "rgb(230, 230, 230)",
        border: "1px solid rgba(0, 0, 0, 0.2)",
        borderRadius: "8px",
        boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.7)",
        outline: 0,
        overflow: "auto",
        padding: "20px",
      }}
    >
      <h2>Enter Report Name</h2>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Type report name..."
        style={{
          padding: "8px",
          margin: "10px 0",
          border: "1px solid #ccc",
          borderRadius: "4px",
        }}
      />
      <button
        onClick={handleSave}
        style={{
          padding: "8px 16px",
          backgroundColor: "#007bff",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        Save
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {savedReportId && (
        <p style={{ color: "green" }}>Report saved</p>
      )}
    </div>
  );
};

export default ReportSave;

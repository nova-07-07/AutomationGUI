import React, { useState } from "react";

function FolderView({ folderData, setSelectedFile }) {
  const [isOpen, setOpen] = useState(false);

  if (!folderData || !folderData.items) {
    return <p style={{ fontSize: "18px" }}>No items found in this folder.</p>;
  }

  // Function to get the correct file icon based on extension
  const getFileIcon = (filename) => {
    if (filename.endsWith(".py")) return "/pythonImg.png";
    if (filename.endsWith(".feature")) return "/cucumber.png";
    if (filename.endsWith(".java")) return "/Javap.png";
    return "/defaultFile.png"; // Default file icon
  };

  return (
    <div style={{ cursor: "pointer", fontSize: "20px" }}>
      <h3 onClick={() => setOpen(!isOpen)} style={{ fontSize: "22px" }}>
        {"📂"} {folderData.name}
      </h3>
      {isOpen && (
        <ul style={{ marginLeft: "25px" }}>
          {folderData.items.map((item, index) => (
            <li key={index} style={{ listStyleType: "none", display: "flex", alignItems: "center", marginBottom: "8px" }}>
              {item.isfolder ? (
                <FolderView folderData={item} setSelectedFile={setSelectedFile} />
              ) : (
                <>
                  <img
                    src={getFileIcon(item.name)}
                    alt="File Icon"
                    style={{ width: "30px", height: "30px", marginRight: "10px", cursor: "pointer" }}
                    onClick={() => setSelectedFile({ filename: item.name, path: item.path })}
                  />
                  <span
                    onClick={() => setSelectedFile({ filename: item.name, path: item.path })}
                    style={{ color: "blue", textDecoration: "underline", cursor: "pointer" }}
                  >
                    {item.name}
                  </span>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FolderView;

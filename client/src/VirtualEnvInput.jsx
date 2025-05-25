import { useEffect, useState } from "react";
import axios from "axios";
import "./VirtualEnvInput.css";
import List_item from "./List_item";
import { useNavigate } from "react-router-dom";

export default function VirtualEnvInput({ setEnvPath, setGetEnv, envPath , backgroundSelect  }) {
  const [path, setPath] = useState("");
  const [items, setItems] = useState([]);
  const [refresh, setRefresh] = useState(false);
  const navigate = useNavigate();

  async function fetchEnvPaths() {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("something is wrong please login again");
      navigate("/signin")
    }
    try {
      const response = await axios.get("http://localhost:5000/get-env-paths", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.data.env_paths) {
        setItems(response.data.env_paths.map((path) => [path.split(/[\\/]/).pop(), path]));
      }
    } catch (err) {
      console.error("Error fetching environment paths:", err);
    }
  }

  useEffect(() => {
    fetchEnvPaths();
    console.log(items);;
  }, [refresh]);

  async function handleSetEnvPath() {
    if (!path.trim()) {
      alert("Please enter a valid path.");
      return;
    }

    const token = localStorage.getItem("token");
    try {
      const response = await axios.get(
        `http://localhost:5000/get-folder?path=${encodeURIComponent(path)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.data.error) {
        alert("Path does not exist");
        setPath("");
        return;
      }

      if (response.data.path) {
        const newPath = response.data.path;
        console.log(newPath);
        
        const newName = newPath.split(/[\\/]/).pop();

        if (items.some(([_, existingPath]) => existingPath === newPath)) {
          alert("This path already exists");
          setPath("");
          return;
        }

        await axios.post(
          "http://localhost:5000/update-env-path",
          { env_path: newPath },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        setRefresh((prev) => !prev); // Trigger re-fetch
      }
    } catch (err) {
      console.error("Error fetching folder data or updating backend:", err);
    }

    setPath("");
  }

  async function handleDelete(index) {
    const token = localStorage.getItem("token");
    const envPathToRemove = items[index][1];

    try {
      await axios.delete("http://localhost:5000/remove-env-path", {
        headers: { Authorization: `Bearer ${token}` },
        data: { env_path: envPathToRemove },
      });

      setRefresh((prev) => !prev);
    } catch (err) {
      console.error("Error removing environment path:", err);
      alert("Failed to remove the environment path. Please try again.");
    }
  }

  function handleUse(item) {
    setEnvPath(item);
    setGetEnv(false);
    backgroundSelect(false);
  }

  return (
    <div className="container-new">
      <div className="nav">
        <h2>Environments</h2>
        <div>
          <input
            className="path_in"
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="Path to virtual env"
          />
          <button className="addBtn" onClick={handleSetEnvPath}>Add</button>
        </div>
      </div>
      <div className="bod">
        <List_item envPath={envPath} items={items} handleDelete={handleDelete} handleUse={handleUse} />
      </div>
    </div>
  );
}

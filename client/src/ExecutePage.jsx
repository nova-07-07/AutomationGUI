import "./App.css";
import axios from "axios";
import { useState, useRef, useEffect } from "react";
import FolderView from "./FolderView";
import VirtualEnvInput from "./VirtualEnvInput.jsx";
import SettingsMenu from "./SettingsMenu";
import ReportSave from "./ReportSave.jsx";
import ReportShow from "./ReportShow.jsx";
import './ExecutePage.css'
import DisplayArguments from "./DisplayArguments.jsx";
import {  useNavigate } from "react-router-dom";

function ExecutePage() {
  const [path, setPath] = useState("");
  const [folderData, setFolderData] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [flode, setFlode] = useState(false);
  const [getenv, setGetEnv] = useState(false);
  const [showReportSave ,SetShowReportSave] = useState(false);
  const [showReportShow ,SetShowReportShow] = useState(false);
  const [envpath, setEnvPath] = useState("");
  const cancelTokenSource = useRef(null);
  const [disBlack , setDisplayBlack] = useState(false);
  const [testType , setTestType] = useState("python");
  const [settingExit , setSettingExit] = useState(false);
  const [argObject , setArgObj] = useState([]);
  const [displayArgComp , setDisplayArgComp] = useState(false);
  const [argArray , setArgArray] = useState([]);
  const [argInputs , setArgInput] = useState([]);
  const [disW,setDispW] = useState(false);
  const [disSet , setDisSet] = useState(false);
  const navigate = useNavigate();

  if (!localStorage.getItem("token")) {
    navigate("/signin")
  }
  function backgroundSelect() {
        SetShowReportSave(false);
        SetShowReportShow(false);
        setGetEnv(false);
        setDisplayBlack(false)
        setSettingExit(false);
        setDisplayArgComp(false);
        setDispW(false);
        setSettingExit(!settingExit);
  }
  
  useEffect(()=>{
    if (disSet) {
      setDispW(true);
    }else{
      setDispW(false);
    }    
  },[disSet])

  useEffect(()=>{
    if (!selectedFile?.path) {
      setOutput("Select File and click Run");
    }else {
      setOutput("Click Run to run the selected file.")
    }
    
  },[envpath])

  useEffect(()=>{
    setSettingExit(!settingExit);
  },[settingExit])

  const fetchFolders = async () => {
    if (!path.trim()) {
      alert("Please enter a valid path.");
      return;
    }
  
    setOutput("");
    setArgObj([]);
    setArgArray([]);
    setArgInput([]);
    setSelectedFile("");
    setFlode(true);
    const token = localStorage.getItem("token");

    try {
      const response = await axios.get(
        `http://localhost:5000/get-folder?path=${encodeURIComponent(path)}&testType=${encodeURIComponent(testType)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
  
      const data = response.data;
  
      if (!data || !data.items || data.items.length === 0) {
        // Don't store path if data is empty or invalid
        alert("No folders found in the given path.");
        setFolderData(null);
        setFlode(false);
        return;
      }
  
      setFolderData(data);
  
      // Traverse folder structure to find conftest.py
      function findConftestPaths(obj) {
        let result = [];
  
        function traverse(node) {
          if (!node || !node.items) return;
  
          for (let item of node.items) {
            if (!item.isfolder && item.name === "conftest.py") {
              result.push(item.path);
            } else if (item.isfolder) {
              traverse(item);
            }
          }
        }
  
        traverse(obj);
        return result;
      }
  
      const conftestPaths = findConftestPaths(data);
      setArgObj(conftestPaths);
      console.log("conftest paths:", conftestPaths);
  
      // Only store the path if everything is valid
      try {
        const storeResponse = await axios.post(
          "http://localhost:5000/store-used-path",
          { used_path: path },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
  
        if (!storeResponse.data.message) {
          console.log("Warning: Path stored but no message returned.");
        }
      } catch (error) {
        console.error("Error storing used path:", error);
      }
  
    } catch (error) {
      console.error("Error fetching folders:", error);
  
      if (error.response?.status === 401) {
        alert("Unauthorized access! Please log in again.");
        localStorage.removeItem("token");
        navigate("/");
      } else {
        setFolderData(null);
      }
    }
  
    setFlode(false);
  };

  const executePythonFile = async () => {
    if (!selectedFile?.path) {
      setOutput("No file selected.");
      return;
    }
    if (!envpath) {
      setGetEnv(true);
      setDisplayBlack(true);
      return;
    }
  
    if (argObject.length !== 0) {
      let Argpath = null;
      
  
      for (const element of argObject) {
        if (element.replace(/\\conftest\.py$/, '') === selectedFile.path.replace(/\\[^\\]*\.py$/, '')) {
          try {
            const token = localStorage.getItem("token");
            const response = await axios.post(
              "http://localhost:5000/chech_arg",
              { path: element },
              { headers: { Authorization: `Bearer ${token}` } }
            );
  
            Argpath = element;
            setArgArray(response.data);
          } catch (error) {
            console.error("Execution error", error);
            setOutput("Execution error", error);
            setLoading(false);
            return
          }
        }
      }
  
      if (Argpath) {
        setDisplayArgComp(true);
        return;
      }
    }
    startExecution(envpath);
  };

  const startExecution = async (envPath) => {
    if (!envPath) {
      setOutput("No virtual environment path provided.");
      return;
    }

    setEnvPath(envPath);
    setGetEnv(false);

    if (loading) {
      cancelTokenSource.current?.cancel("Execution stopped by user.");
      setLoading(false);
      setOutput("Execution stopped.");
      return;
    }

    setLoading(true);
    setOutput("");
    if (testType == "e") {
      alert("please enter test type");
      return;
    }
    cancelTokenSource.current = axios.CancelToken.source();

    try {
      const token = localStorage.getItem("token");
      const args = argObject !== 0 ? argInputs : {};  
      const response = await axios.post(
        "http://localhost:5000/execute-script",
        { file_path: selectedFile.path, env_path: envPath ,testType : testType ,arg: args},
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          cancelToken: cancelTokenSource.current.token,
        }
      );

      setOutput(response.data.stdout || response.data.stderr || "No output");
    } catch (error) {
      console.error("Execution error", error);

      if (error.response?.status === 401) {
        alert("Unauthorized access! Please log in again.");
        localStorage.removeItem("token");
        setOutput("UNAUTHORIZED");
      } else {
        setOutput("Execution failed: " + (error.response?.data?.error || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  const divider = document.getElementById("drag-divider");
  const left = divider?.previousElementSibling;
  const right = divider?.nextElementSibling;

  let isDragging = false;

  const handleMouseDown = (e) => {
    isDragging = true;
    document.body.style.cursor = "col-resize";
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    const containerWidth = divider.parentNode.offsetWidth;
    const leftWidth = e.clientX;
    const rightWidth = containerWidth - leftWidth - divider.offsetWidth;

    if (leftWidth > 100 && rightWidth > 100) {
      left.style.width = `${leftWidth}px`;
      right.style.width = `${rightWidth}px`;
    }
  };

  const handleMouseUp = () => {
    isDragging = false;
    document.body.style.cursor = "default";
  };

  divider?.addEventListener("mousedown", handleMouseDown);
  window.addEventListener("mousemove", handleMouseMove);
  window.addEventListener("mouseup", handleMouseUp);

  

  return () => {
    divider?.removeEventListener("mousedown", handleMouseDown);
    window.removeEventListener("mousemove", handleMouseMove);
    window.removeEventListener("mouseup", handleMouseUp);
  };
}, []);

function handleClickGoHomePage() {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Unauthorized access! Please log in again.");
      localStorage.removeItem("token");
      navigate("/signin");
    } else {
      navigate("/home_page");
    }
  }
  return (
    <>
    
     <div 
      style={{ opacity: disBlack ? 0.2 : 1 }} 
      onClick={() => {
        if (disBlack) {
          backgroundSelect();
        }
      }}
    >

        <div className="nav">
        <div className="nav_one" style={{ display: "flex" }}>
          
        <span className="hed" onClick={() => {
          window.history.pushState(null, "", "/home_page");
          window.location.reload();
        }}>
          Test Execution GUI
        </span>

            <div className="inputdev">
              <input
                type="text"
                className="pathIn"
                placeholder="Enter folder path or git URL"
                value={path}
                onChange={(e) => setPath(e.target.value)}
              />
              <button className="gobtn" onClick={fetchFolders}>
                <b>Go</b>
              </button>
            </div>
          </div>
          <div className="nav_two">
            <b className="run_set"> 
              <div>
                  <span className="hee">{selectedFile?.filename || "No file selected"}</span>
                <button
                  className="run-btn"
                  onClick={executePythonFile}
                  disabled={loading && !cancelTokenSource.current}
                >
                  {loading ? "Stop" : "Run"}
                </button>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <SettingsMenu 
                  SetShowReportSave={SetShowReportSave} 
                  setGetEnv={setGetEnv} 
                  SetShowReportShow={SetShowReportShow} 
                  setDisplayBlack={setDisplayBlack} 
                  setTestType={setTestType}
                  SetDisplayBlack={setDisplayBlack}
                  settingExit={settingExit}
                  setSettingExit={setSettingExit}
                  setDisSet={setDisSet}
                />
              </div>
            </b>
            </div>
        </div>

        <div className="mainbody" onClick={() => {
          if(settingExit){
          backgroundSelect()
          }
        }}>
          <div className="split-container">
            <div className="left">
              {flode ? (
                <h1>Loading...</h1>
              ) : (
                <FolderView folderData={folderData || {}} setSelectedFile={setSelectedFile} />
              )}
            </div>

            <div className="divider" id="drag-divider"></div>

            <div className="right">
              {selectedFile ? (
                <div className="right-1">
                  <h2 className="ter-tit">Output</h2>
                  <pre className="output">
                    {loading ? "Running..." : `${output}`}
                  </pre>
                </div>
              ) : (
                <h1 className="ter-tit">Click a Python file to select</h1>
              )}
            </div>
          </div>

        </div>
      </div>

      {getenv && <VirtualEnvInput setEnvPath={setEnvPath} setGetEnv={setGetEnv} envPath={envpath} backgroundSelect={backgroundSelect} />}
      {showReportSave && <ReportSave SetShowReportSave={SetShowReportSave} output={output} backgroundSelect={backgroundSelect}/>}
      { showReportShow && <ReportShow /> }
      { displayArgComp && <DisplayArguments argArray={argArray} setArgInput={setArgInput} argInputs={argInputs} startExecution={startExecution} envpath={envpath} setDisplayArgComp={setDisplayArgComp} setDisplayBlack={setDisplayBlack}/>}
      
    </>
  );
}

export default ExecutePage;

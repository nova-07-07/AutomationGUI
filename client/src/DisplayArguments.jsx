import React, { useEffect, useState } from "react";
import "./DisplayItems.css"; 

const DisplayArguments = ({ argArray, setArgInput, argInputs, startExecution, envpath, setDisplayArgComp, setDisplayBlack }) => {
  const [items, setItems] = useState([]);
  const [values, setValues] = useState([]);

  // Move setDisplayBlack inside useEffect to prevent re-renders
  useEffect(() => {
    setDisplayBlack(true);
  }, [setDisplayBlack]);

  useEffect(() => {
    const res = argArray.map((val) => val[0]);
    setItems(res);
    setValues(res.map((val) => [val, ""]));
    setArgInput(res.map((val) => [val, ""])); 
  }, [argArray, setArgInput]);

  function handleUse() {
    for (let vv of values) {
      if (vv[1] === "") {
        alert(`${vv[0]} value is empty.`);
        return;
      }
    }
    
    startExecution(envpath);
    setDisplayArgComp(false);
    setDisplayBlack(false);
  }  

  function handleChange(index, val) {
    setValues((prevValues) =>
      prevValues.map((item, i) => (i === index ? [item[0], val] : item))
    );
    
    setArgInput((prevValues) =>
      prevValues.map((item, i) => (i === index ? [item[0], val] : item))
    );
  }

  return (
    <div className="main_container_dis-arg">
      <div className="nav_arg">
        <h2 className="tt-Arg">Arguments</h2>
        <button className="uBtn" onClick={handleUse}>Use</button>
      </div>
      <div className="boddd">
      {items.map((item, index) => (
        <div key={index} className="item_arg">
          {item.replace("--", "")}
          <h1>:</h1>
          <input
            className="input_val"
            type="text"
            value={argInputs[index]?.[1] || ""}
            onChange={(e) => handleChange(index, e.target.value)}
          />
        </div>
      ))}</div>
    </div>
  );
};

export default DisplayArguments;

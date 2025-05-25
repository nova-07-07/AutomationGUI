import React from "react";
import "./VirtualEnvInput.css";

const List_item = ({ items, handleDelete, handleUse, envPath }) => {
  console.log(envPath);
  
  return (
    <div className="ul_l">
      {items.map((item, index) => (
        <div
          className="li_l"
          style={item[1] === envPath ? { backgroundColor: "burlywood"} : {}}
          key={index}
        >
          <span className="indexno">{index + 1}</span>
          <span className="">{item[0]}</span> 
          <div className="btns">
            <button className="deletebtn" onClick={() => handleDelete(index)}>Remove</button> 
            <button className="usebtn" style={{ border: item[1] === envPath ? "none" : "2px solid blue" }}  onClick={() => item[1] !== envPath && handleUse(item[1])}>{item[1] == envPath ? <span className="gg"></span> : <span>Use</span>}</button>     
          </div>
        </div>
      ))}
    </div>
  );
};

export default List_item;

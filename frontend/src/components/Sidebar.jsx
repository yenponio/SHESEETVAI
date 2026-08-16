import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import "./Sidebar.css";

import {
  FaBars,
  FaHome,
  FaClipboardList,
  FaCheckCircle,
  FaSignOutAlt,
} from "react-icons/fa";

function Sidebar() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("osaLoggedIn");
    navigate("/osa");
  };

  return (
    <div className={open ? "sidebar open" : "sidebar"}>
      <button
        className="menuBtn"
        onClick={() => setOpen(!open)}
      >
        <FaBars />
      </button>

      <nav className="menu">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            isActive ? "menuItem active" : "menuItem"
          }
        >
          <FaHome className="icon" />
          {open && <span>Home</span>}
        </NavLink>

        <NavLink
          to="/records"
          className={({ isActive }) =>
            isActive ? "menuItem active" : "menuItem"
          }
        >
          <FaClipboardList className="icon" />
          {open && <span>Records</span>}
        </NavLink>

        <NavLink
          to="/chatbot"
          className={({ isActive }) =>
            isActive ? "menuItem active" : "menuItem"
          }
        >
          <FaCheckCircle className="icon" />
          {open && <span>Chatbot</span>}
        </NavLink>
      </nav>

      <button
        className="logoutBtn"
        onClick={handleLogout}
      >
        <FaSignOutAlt className="icon" />
        {open && <span>Logout</span>}
      </button>
    </div>
  );
}

export default Sidebar;
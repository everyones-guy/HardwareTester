import React from "react";
import { NavLink } from "react-router-dom";
import {
    FaMicrochip,
    FaNetworkWired,
    FaFlask,
    FaUser,
    FaHdd,
    FaCodeBranch,
    FaChartBar,
} from "react-icons/fa";
import "./Sidebar.css";

const Sidebar: React.FC = () => {
    return (
        <div className="sidebar">
            <h2 className="sidebar-title">Hardware Tester</h2>

            <nav className="sidebar-nav">
                <NavLink to="/emulator" className="nav-item">
                    <FaMicrochip /> <span>Emulator</span>
                </NavLink>
                <NavLink to="/connect" className="nav-item">
                    <FaNetworkWired /> <span>Connect</span>
                </NavLink>
                <NavLink to="/tests" className="nav-item">
                    <FaFlask /> <span>Tests</span>
                </NavLink>
                <NavLink to="/user-management" className="nav-item">
                    <FaUser /> <span>Users</span>
                </NavLink>
                <NavLink to="/user" className="nav-item">
                    <FaUser /> <span>User</span>
                </NavLink>
                <NavLink to="/hardware" className="nav-item">
                    <FaHdd /> <span>Hardware</span>
                </NavLink>
                <NavLink to="/firmware" className="nav-item">
                    <FaCodeBranch /> <span>Firmware</span>
                </NavLink>
                <NavLink to="/metrics" className="nav-item">
                    <FaChartBar /> <span>Metrics</span>
                </NavLink>
            </nav>
        </div>
    );
};

export default Sidebar;

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
                <NavLink to="/legacy/emulator" className="nav-item">
                    <FaMicrochip /> <span>Emulator</span>
                </NavLink>
                <NavLink to="/legacy/connect" className="nav-item">
                    <FaNetworkWired /> <span>Connect</span>
                </NavLink>
                <NavLink to="/legacy/tests" className="nav-item">
                    <FaFlask /> <span>Tests</span>
                </NavLink>
                <NavLink to="/legacy/user-management" className="nav-item">
                    <FaUser /> <span>Users</span>
                </NavLink>
                <NavLink to="/legacy/user" className="nav-item">
                    <FaUser /> <span>User</span>
                </NavLink>
                <NavLink to="/legacy/hardware" className="nav-item">
                    <FaHdd /> <span>Hardware</span>
                </NavLink>
                <NavLink to="/legacy/firmware" className="nav-item">
                    <FaCodeBranch /> <span>Firmware</span>
                </NavLink>
                <NavLink to="/legacy/metrics" className="nav-item">
                    <FaChartBar /> <span>Metrics</span>
                </NavLink>
            </nav>
        </div>
    );
};

export default Sidebar;

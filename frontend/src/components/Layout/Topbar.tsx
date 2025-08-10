import React from "react";
import { FaUserCircle } from "react-icons/fa";
import "./Topbar.css";

const Topbar: React.FC = () => {
    return (
        <div className="topbar">
            <div className="topbar-left">
                <h1 className="topbar-title">Universal Hardware Tester</h1>
            </div>

            <div className="topbar-right">
                {/* Future enhancements */}
                <span className="user-info">
                    <FaUserCircle size={20} />
                    <span className="username">Admin</span>
                </span>
            </div>
        </div>
    );
};

export default Topbar;

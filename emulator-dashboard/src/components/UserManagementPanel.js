import React, { useState, useEffect } from "react";
import { getUserProfile, logoutUser } from "../services/authService";

const UserManagementPanel = () => {
    const [user, setUser] = useState(null);

    useEffect(() => {
        fetchUserProfile();
    }, []);

    const fetchUserProfile = async () => {
        const data = await getUserProfile();
        setUser(data);
    };

    const handleLogout = async () => {
        await logoutUser();
        setUser(null);
    };

    return (
        <div className="user-management-panel">
            <h2>User Management</h2>
            {user ? (
                <div>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Role:</strong> {user.role}</p>
                    <button onClick={handleLogout}>Logout</button>
                </div>
            ) : (
                <p>No user logged in.</p>
            )}
        </div>
    );
};

export default UserManagementPanel;

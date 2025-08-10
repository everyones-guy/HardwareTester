// src/components/User/UserProfile.tsx
import React from "react";

const UserProfile: React.FC = () => {
    return (
        <div className="user-profile">
            <h2>My Profile</h2>
            <p>Username: gary</p>
            <p>Email: gary@example.com</p>
            <button>Edit Profile</button>
        </div>
    );
};

export default UserProfile;
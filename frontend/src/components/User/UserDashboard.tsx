// src/components/User/UserDashboard.tsx
import React from "react";
import UserManagementPanel from "./UserManagementPanel";
import UserProfile from "./UserProfile";
import UserRoleManager from "./UserRoleManager";
import AccessAuditLog from "./AccessAuditLog";
import InviteUserModal from "./InviteUserModal";
import SessionMonitor from "./SessionMonitor";

const UserDashboard: React.FC = () => {
    return (
        <div className="user-dashboard">
            <h1>User Dashboard</h1>
            <UserProfile />
            <UserManagementPanel />
            <UserRoleManager />
            <InviteUserModal />
            <AccessAuditLog />
            <SessionMonitor />
        </div>
    );
};

export default UserDashboard;
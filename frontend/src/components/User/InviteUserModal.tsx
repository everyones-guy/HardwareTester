// src/components/User/InviteUserModal.tsx
import React, { useState } from "react";

const InviteUserModal: React.FC = () => {
    const [email, setEmail] = useState("");

    const handleInvite = () => {
        alert(`Invite sent to ${email}`);
        setEmail("");
    };

    return (
        <div className="invite-user-modal">
            <h2>Invite New User</h2>
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email address"
            />
            <button onClick={handleInvite}>Send Invite</button>
        </div>
    );
};

export default InviteUserModal;
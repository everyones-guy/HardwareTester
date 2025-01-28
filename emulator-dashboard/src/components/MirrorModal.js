import React, { useState, useEffect } from "react";
import { io } from "socket.io-client";

const MirrorModal = ({ topic, onClose }) => {
    const [commands, setCommands] = useState([]);
    const socket = io("http://localhost:5000");

    useEffect(() => {
        socket.emit("start_mirror", { topic });

        socket.on("mirror_update", (data) => {
            setCommands((prev) => [...prev, data]);
        });

        return () => socket.disconnect();
    }, [topic]);

    return (
        <div className="modal">
            <h2>Mirror Mode: {topic}</h2>
            <ul>
                {commands.map((cmd, index) => (
                    <li key={index}>{cmd.command}</li>
                ))}
            </ul>
            <button onClick={onClose}>Close</button>
        </div>
    );
};

export default MirrorModal;

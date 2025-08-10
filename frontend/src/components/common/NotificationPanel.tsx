// src/components/Common/NotificationPanel.tsx
import React, { useEffect, useState } from "react";
import {
    getNotifications,
    markNotificationAsRead,
    deleteNotification,
    subscribeToNotifications,
} from "@/services/notificationService";
import { Notification } from "@/types/notificationTypes";
import "./NotificationPanel.css";

const NotificationPanel: React.FC = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);

    useEffect(() => {
        loadNotifications();
        const unsubscribe = subscribeToNotifications((msg: Notification) => {
            setNotifications((prev) => [msg, ...prev]);
        });
        return () => unsubscribe();
    }, []);

    const loadNotifications = async () => {
        const data = await getNotifications();
        setNotifications(data);
    };

    const handleRead = async (id: string) => {
        await markNotificationAsRead(id);
        setNotifications((prev) =>
            prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
        );
    };

    const handleDelete = async (id: string) => {
        await deleteNotification(id);
        setNotifications((prev) => prev.filter((n) => n.id !== id));
    };

    return (
        <div className="notification-panel">
            <h2>Notifications</h2>
            {notifications.length === 0 ? (
                <p>No notifications yet.</p>
            ) : (
                <ul>
                    {notifications.map((n) => (
                        <li key={n.id} className={`notification ${n.type} ${n.isRead ? "read" : ""}`}>
                            <div className="notification-content">
                                <strong>{n.title}</strong>
                                <p>{n.message}</p>
                                <small>{new Date(n.timestamp).toLocaleString()}</small>
                            </div>
                            <div className="notification-actions">
                                {!n.isRead && (
                                    <button onClick={() => handleRead(n.id)}>Mark as Read</button>
                                )}
                                <button onClick={() => handleDelete(n.id)}>Delete</button>
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default NotificationPanel;

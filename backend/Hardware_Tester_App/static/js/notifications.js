document.addEventListener("DOMContentLoaded", () => {
    const notificationList = document.getElementById("notifications-list");
    const addNotificationForm = document.getElementById("add-notification-form");

    /**
     * Fetch and display notifications
     */
    async function loadNotifications() {
        try {
            const data = await apiCall("/notifications/list", "GET");

            notificationList.innerHTML = "";
            if (data.success && data.notifications.length > 0) {
                data.notifications.forEach((notification) => {
                    notificationList.innerHTML += `
                        <li class="list-group-item">
                            <strong>${notification.title}</strong> - ${notification.message}
                            <span class="badge bg-${notification.type} float-end">${notification.type}</span>
                            <button class="btn btn-sm btn-danger float-end mx-2 delete-notification" data-id="${notification.id}">Delete</button>
                        </li>`;
                });

                attachDeleteListeners();
            } else {
                notificationList.innerHTML = `<li class="list-group-item text-danger">No notifications available.</li>`;
            }
        } catch (error) {
            console.error("Error fetching notifications:", error);
            notificationList.innerHTML = `<li class="list-group-item text-danger">Failed to load notifications.</li>`;
        }
    }

    /**
     * Handle notification addition
     */
    if (addNotificationForm) {
        addNotificationForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const formData = new FormData(addNotificationForm);
            const payload = Object.fromEntries(formData.entries());

            try {
                const response = await apiCall("/notifications/add", "POST", payload);
                alert(response.message || "Notification added successfully!");
                addNotificationForm.reset();
                loadNotifications();
            } catch (error) {
                console.error("Error adding notification:", error);
                alert("Failed to add notification. Please try again.");
            }
        });
    }

    /**
     * Attach delete listeners dynamically
     */
    function attachDeleteListeners() {
        document.querySelectorAll(".delete-notification").forEach((button) => {
            button.addEventListener("click", async () => {
                const notificationId = button.getAttribute("data-id");

                if (confirm("Are you sure you want to delete this notification?")) {
                    try {
                        const response = await apiCall(`/notifications/delete/${notificationId}`, "DELETE");
                        alert(response.message || "Notification deleted.");
                        loadNotifications();
                    } catch (error) {
                        console.error("Error deleting notification:", error);
                        alert("Failed to delete notification.");
                    }
                }
            });
        });
    }

    // **Initial Load**
    loadNotifications();
});

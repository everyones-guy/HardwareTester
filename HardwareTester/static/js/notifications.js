
// Fetch and display notifications
function loadNotifications() {
    $.getJSON("/notifications/list", function (data) {
        const list = $("#notifications-list");
        list.empty();
        if (data.success) {
            data.notifications.forEach((notification) => {
                list.append(
                    `<li class="list-group-item">
                        <strong>${notification.title}</strong> - ${notification.message}
                        <span class="badge bg-${notification.type} float-end">${notification.type}</span>
                        <button class="btn btn-sm btn-danger float-end mx-2" onclick="deleteNotification(${notification.id})">Delete</button>
                    </li>`
                );
            });
        } else {
            list.append(`<li class="list-group-item text-danger">${data.error}</li>`);
        }
    });
}

// Handle notification addition
function handleAddNotification() {
    $("#add-notification-form").on("submit", function (event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        const payload = {};
        formData.forEach((item) => (payload[item.name] = item.value));
        $.ajax({
            url: "/notifications/add",
            type: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": $('meta[name="csrf-token"]').attr('content')  // Ensure CSRF token is sent
            },
            data: JSON.stringify(payload),
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    loadNotifications();
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
        });
    });
}

// Delete a notification
function deleteNotification(notificationId) {
    if (confirm("Are you sure you want to delete this notification?")) {
        $.ajax({
            url: `/notifications/delete/${notificationId}`,
            type: "DELETE",
            headers: {
                "X-CSRFToken": $('meta[name="csrf-token"]').attr('content')  // Ensure CSRF token is sent
            },
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    loadNotifications();
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
        });
    }
}

// Initialize scripts
$(document).ready(function () {
    loadNotifications();
    handleAddNotification();
});


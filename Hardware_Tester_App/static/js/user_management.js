// Fetch and display the list of users
function loadUsers() {
    $.getJSON("/users/list", function (data) {
        const list = $("#user-list");
        list.empty();
        if (data.success) {
            data.users.forEach((user) => {
                list.append(
                    `<li class="list-group-item">
                        <strong>${user.username}</strong> - ${user.email}
                        <button class="btn btn-sm btn-danger float-end delete-user" data-id="${user.id}">Delete</button>
                    </li>`
                );
            });
        } else {
            list.append(`<li class="list-group-item text-danger">${data.error}</li>`);
        }
    });
}

// Handle user addition
function handleAddUser() {
    $("#add-user-form").on("submit", function (event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        const payload = {};
        formData.forEach((item) => (payload[item.name] = item.value));
        $.ajax({
            url: "/users/add",
            type: "POST",
            headers: {
                "X-CSRFToken": $("meta[name='csrf-token']").attr("content")  // Ensure CSRF token is sent
            },
            contentType: "application/json",
            data: JSON.stringify(payload),
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    loadUsers();
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
            error: function (xhr) {
                alert(`Error: ${xhr.statusText}`);
            }
        });
    });
}

// Delete a user
function deleteUser(userId) {
    if (confirm("Are you sure you want to delete this user?")) {
        $.ajax({
            url: `/users/delete/${userId}`,
            type: "DELETE",
            headers: {
                "X-CSRFToken": $("meta[name='csrf-token']").attr("content")  // Ensure CSRF token is sent
            },
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    loadUsers();
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
            error: function (xhr) {
                alert(`Error: ${xhr.statusText}`);
            }
        });
    }
}

// Initialize scripts
$(document).ready(function () {
    loadUsers();
    handleAddUser();

    // Delegate delete user click event to dynamically added elements
    $("#user-list").on("click", ".delete-user", function () {
        const userId = $(this).data("id");
        deleteUser(userId);
    });
});

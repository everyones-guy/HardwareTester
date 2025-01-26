$(document).ready(function () {
    const csrfToken = $("meta[name='csrf-token']").attr("content");

    // Fetch and display saved SSH connections
    function fetchConnections() {
        apiCall("/ssh/connections", "GET", null, (data) => {
            const connectionList = $("#ssh-connection-list");
            connectionList.empty();

            if (data.success && data.connections.length > 0) {
                data.connections.forEach((connection) => {
                    connectionList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <strong>${connection.name}</strong>
                            <div>
                                <button class="btn btn-primary btn-sm edit-ssh-connection" data-id="${connection.id}">Edit</button>
                                <button class="btn btn-danger btn-sm delete-ssh-connection ms-2" data-id="${connection.id}">Delete</button>
                            </div>
                        </li>
                    `);
                });
            } else {
                connectionList.html("<li class='list-group-item text-center'>No connections available.</li>");
            }
        });
    }

    // Add a new SSH connection
    $("#add-ssh-connection-form").on("submit", function (event) {
        event.preventDefault();

        const data = {
            name: $("#connection-name").val(),
            host: $("#host").val(),
            port: $("#port").val(),
            username: $("#username").val(),
            password: $("#password").val(),
        };

        apiCall("/ssh/connection", "POST", data, (response) => {
            showAlert(response.message || "Connection added successfully.", "success");
            $("#add-ssh-connection-modal").modal("hide");
            fetchConnections();
        });
    });

    // Edit an SSH connection
    $(document).on("click", ".edit-ssh-connection", function () {
        const connectionId = $(this).data("id");

        apiCall(`/ssh/connection/${connectionId}`, "GET", null, (data) => {
            if (data.success) {
                const connection = data.connection;
                $("#edit-connection-name").val(connection.name);
                $("#edit-host").val(connection.host);
                $("#edit-port").val(connection.port);
                $("#edit-username").val(connection.username);
                $("#edit-password").val(""); // Passwords should not be prefilled

                $("#edit-ssh-connection-form").off("submit").on("submit", function (event) {
                    event.preventDefault();

                    const updatedData = {
                        name: $("#edit-connection-name").val(),
                        host: $("#edit-host").val(),
                        port: $("#edit-port").val(),
                        username: $("#edit-username").val(),
                        password: $("#edit-password").val(),
                    };

                    apiCall(`/ssh/connection/${connectionId}`, "POST", updatedData, (response) => {
                        showAlert(response.message || "Connection updated successfully.", "success");
                        $("#edit-ssh-connection-modal").modal("hide");
                        fetchConnections();
                    });
                });

                $("#edit-ssh-connection-modal").modal("show");
            }
        });
    });

    // Delete an SSH connection
    $(document).on("click", ".delete-ssh-connection", function () {
        const connectionId = $(this).data("id");

        if (confirm("Are you sure you want to delete this connection?")) {
            apiCall(`/ssh/connection/${connectionId}`, "DELETE", null, (response) => {
                showAlert(response.message || "Connection deleted successfully.", "success");
                fetchConnections();
            });
        }
    });

    // Test SSH connection
    $("#test-ssh-connection-form").on("submit", function (event) {
        event.preventDefault();

        const data = {
            host: $("#test-host").val(),
            port: $("#test-port").val(),
            username: $("#test-username").val(),
            password: $("#test-password").val(),
        };

        apiCall("/ssh/test", "POST", data, (response) => {
            const testResults = $("#test-results");
            if (response.success) {
                testResults.html(`<p class="text-success">Connection successful!</p>`);
                showAlert("SSH connection test successful.", "success");
            } else {
                testResults.html(`<p class="text-danger">Connection failed: ${response.error}</p>`);
                showAlert("SSH connection test failed.", "danger");
            }
        });
    });

    // Refresh connections
    $("#refresh-ssh-connections").on("click", function () {
        fetchConnections();
    });

    // Initial load
    fetchConnections();
});

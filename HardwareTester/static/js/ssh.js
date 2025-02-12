document.addEventListener("DOMContentLoaded", () => {
    const sshConnectionsList = document.getElementById("ssh-connection-list");
    const addSSHForm = document.getElementById("add-ssh-connection-form");
    const editSSHForm = document.getElementById("edit-ssh-connection-form");
    const testSSHForm = document.getElementById("test-ssh-connection-form");

    /**
     * Fetch and display saved SSH connections.
     */
    async function fetchConnections() {
        try {
            const data = await apiCall("/ssh/connections", "GET");

            sshConnectionsList.innerHTML = "";
            if (data.success && data.connections.length > 0) {
                data.connections.forEach((connection) => {
                    sshConnectionsList.innerHTML += `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <strong>${connection.name}</strong>
                            <div>
                                <button class="btn btn-primary btn-sm edit-ssh-connection" data-id="${connection.id}">Edit</button>
                                <button class="btn btn-danger btn-sm delete-ssh-connection ms-2" data-id="${connection.id}">Delete</button>
                            </div>
                        </li>`;
                });
            } else {
                sshConnectionsList.innerHTML = "<li class='list-group-item text-center'>No SSH connections available.</li>";
            }
        } catch (error) {
            console.error("Error fetching SSH connections:", error);
            alert("Failed to load SSH connections.");
        }
    }

    /**
     * Add a new SSH connection.
     */
    if (addSSHForm) {
        addSSHForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const formData = new FormData(addSSHForm);
            const data = Object.fromEntries(formData);

            try {
                const response = await apiCall("/ssh/connection", "POST", data);
                alert(response.message || "SSH connection added successfully.");
                $("#add-ssh-connection-modal").modal("hide");
                fetchConnections();
            } catch (error) {
                console.error("Error adding SSH connection:", error);
                alert("Failed to add SSH connection.");
            }
        });
    }

    /**
     * Edit an SSH connection.
     */
    document.addEventListener("click", async (event) => {
        if (event.target.classList.contains("edit-ssh-connection")) {
            const connectionId = event.target.dataset.id;

            try {
                const data = await apiCall(`/ssh/connection/${connectionId}`, "GET");

                if (data.success) {
                    const connection = data.connection;
                    document.getElementById("edit-connection-name").value = connection.name;
                    document.getElementById("edit-host").value = connection.host;
                    document.getElementById("edit-port").value = connection.port;
                    document.getElementById("edit-username").value = connection.username;
                    document.getElementById("edit-password").value = ""; // Prevent pre-filling passwords

                    editSSHForm.onsubmit = async function (event) {
                        event.preventDefault();

                        const updatedData = {
                            name: document.getElementById("edit-connection-name").value,
                            host: document.getElementById("edit-host").value,
                            port: document.getElementById("edit-port").value,
                            username: document.getElementById("edit-username").value,
                            password: document.getElementById("edit-password").value,
                        };

                        try {
                            const response = await apiCall(`/ssh/connection/${connectionId}`, "POST", updatedData);
                            alert(response.message || "SSH connection updated successfully.");
                            $("#edit-ssh-connection-modal").modal("hide");
                            fetchConnections();
                        } catch (error) {
                            console.error("Error updating SSH connection:", error);
                            alert("Failed to update SSH connection.");
                        }
                    };

                    $("#edit-ssh-connection-modal").modal("show");
                }
            } catch (error) {
                console.error("Error fetching SSH connection details:", error);
                alert("Failed to fetch SSH connection details.");
            }
        }
    });

    /**
     * Delete an SSH connection.
     */
    document.addEventListener("click", async (event) => {
        if (event.target.classList.contains("delete-ssh-connection")) {
            const connectionId = event.target.dataset.id;

            if (confirm("Are you sure you want to delete this connection?")) {
                try {
                    const response = await apiCall(`/ssh/connection/${connectionId}`, "DELETE");
                    alert(response.message || "SSH connection deleted successfully.");
                    fetchConnections();
                } catch (error) {
                    console.error("Error deleting SSH connection:", error);
                    alert("Failed to delete SSH connection.");
                }
            }
        }
    });

    /**
     * Test an SSH connection.
     */
    if (testSSHForm) {
        testSSHForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const formData = new FormData(testSSHForm);
            const data = Object.fromEntries(formData);

            try {
                const response = await apiCall("/ssh/test", "POST", data);
                const testResults = document.getElementById("test-results");

                if (response.success) {
                    testResults.innerHTML = `<p class="text-success">Connection successful!</p>`;
                    alert("SSH connection test successful.");
                } else {
                    testResults.innerHTML = `<p class="text-danger">Connection failed: ${response.error}</p>`;
                    alert("SSH connection test failed.");
                }
            } catch (error) {
                console.error("Error testing SSH connection:", error);
                alert("Failed to test SSH connection.");
            }
        });
    }

    /**
     * Refresh SSH connections.
     */
    document.getElementById("refresh-ssh-connections").addEventListener("click", () => {
        fetchConnections();
    });

    // **Initial Load**
    fetchConnections();
});

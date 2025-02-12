$(document).ready(function () {
    const hardwareList = $("#hardware-list");
    const testResultsContainer = $("#test-results");
    const firmwareForm = $("#upload-firmware-form");

    /**
     * Fetch and display connected hardware
     */
    async function fetchHardware() {
        try {
            const data = await apiCall("/hardware/list", "GET");

            hardwareList.empty();
            if (data.success) {
                if (data.devices.length > 0) {
                    data.devices.forEach((device) => {
                        hardwareList.append(`
                            <li class="list-group-item">
                                <strong>${device.name}</strong> (${device.type})
                                <span class="badge bg-info">${device.status || "Unknown"}</span>
                                <button class="btn btn-primary btn-sm float-end test-firmware-btn" data-id="${device.id}">Test Firmware</button>
                                <button class="btn btn-secondary btn-sm float-end ssh-connect-btn me-2" data-id="${device.id}">Connect via SSH</button>
                            </li>
                        `);
                    });
                } else {
                    hardwareList.append("<li class='list-group-item text-center'>No devices connected.</li>");
                }
            } else {
                showAlert("Failed to fetch hardware. Please try again.", true);
            }
        } catch (error) {
            console.error("Error fetching hardware:", error);
            showAlert("Error fetching hardware devices.", true);
        }
    }

    /**
     * Test firmware on a device
     */
    $(document).on("click", ".test-firmware-btn", async function () {
        const deviceId = $(this).data("id");

        try {
            const data = await apiCall(`/hardware/${deviceId}/test-firmware`, "POST");

            if (data.success) {
                testResultsContainer.html(`
                    <h5>Firmware Test Results</h5>
                    <pre>${data.results}</pre>
                `);
                showAlert("Firmware test completed successfully.", false);
            } else {
                showAlert("Firmware test failed. Check logs for details.", true);
            }
        } catch (error) {
            console.error("Error testing firmware:", error);
            showAlert("Error testing firmware. Please try again.", true);
        }
    });

    /**
     * Connect to a device via SSH
     */
    $(document).on("click", ".ssh-connect-btn", function () {
        const deviceId = $(this).data("id");

        $("#ssh-modal-body").html(`
            <form id="ssh-credentials-form">
                <div class="mb-3">
                    <label for="username" class="form-label">Username</label>
                    <input type="text" id="username" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Password</label>
                    <input type="password" id="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary">Connect</button>
            </form>
        `);

        const sshModal = new bootstrap.Modal(document.getElementById("ssh-modal"));
        sshModal.show();

        $("#ssh-credentials-form").off("submit").on("submit", async function (event) {
            event.preventDefault();

            const username = $("#username").val();
            const password = $("#password").val();

            try {
                const data = await apiCall(`/hardware/${deviceId}/ssh-connect`, "POST", { username, password });

                if (data.success) {
                    showAlert("SSH connection established.", false);
                    sshModal.hide();
                    executeRemoteCommands(data.commands);
                } else {
                    showAlert("SSH connection failed. Check credentials.", true);
                }
            } catch (error) {
                console.error("Error connecting via SSH:", error);
                showAlert("Error connecting via SSH. Please try again.", true);
            }
        });
    });

    /**
     * Execute remote commands on the device
     */
    async function executeRemoteCommands(commands) {
        for (const command of commands) {
            try {
                const data = await apiCall("/hardware/execute-command", "POST", { command });

                if (data.success) {
                    console.log(`Command "${command}" executed successfully.`);
                } else {
                    console.warn(`Command "${command}" failed: ${data.error}`);
                }
            } catch (error) {
                console.error("Error executing command:", error);
            }
        }
    }

    /**
     * Handle firmware upload
     */
    firmwareForm.on("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(this);

        try {
            await apiCall("/hardware/upload-firmware", "POST", formData);
            showAlert("Firmware uploaded successfully.", false);
            fetchHardware();
        } catch (error) {
            console.error("Error uploading firmware:", error);
            showAlert("Failed to upload firmware. Please try again.", true);
        }
    });

    /**
     * Utility: Show alert messages
     */
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    // Initial fetch
    fetchHardware();
});

$(document).ready(function () {
    const hardwareList = $("#hardware-list");
    const testResultsContainer = $("#test-results");
    const firmwareForm = $("#upload-firmware-form");
    const sshConnectForm = $("#ssh-connect-form");

    // Fetch and display connected hardware
    function fetchHardware() {
        apiCall(
            "/hardware/list",
            "GET",
            null,
            (data) => {
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
                    showAlert("Failed to fetch hardware. Please try again.", "danger");
                }
            },
            (xhr) => {
                console.error("Error fetching hardware:", xhr);
                showAlert("Error fetching hardware devices.", "danger");
            }
        );
    }

    // Test firmware on a device
    $(document).on("click", ".test-firmware-btn", function () {
        const deviceId = $(this).data("id");

        apiCall(
            `/hardware/${deviceId}/test-firmware`,
            "POST",
            null,
            (data) => {
                if (data.success) {
                    testResultsContainer.html(`
                        <h5>Firmware Test Results</h5>
                        <pre>${data.results}</pre>
                    `);
                    showAlert("Firmware test completed successfully.", "success");
                } else {
                    showAlert("Firmware test failed. Check logs for details.", "danger");
                }
            },
            (xhr) => {
                console.error("Error testing firmware:", xhr);
                showAlert("Error testing firmware. Please try again.", "danger");
            }
        );
    });

    // Connect to a device via SSH
    $(document).on("click", ".ssh-connect-btn", function () {
        const deviceId = $(this).data("id");
        const sshForm = `
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
        `;

        $("#ssh-modal-body").html(sshForm);
        const sshModal = new bootstrap.Modal(document.getElementById("ssh-modal"));
        sshModal.show();

        $(document).on("submit", "#ssh-credentials-form", function (event) {
            event.preventDefault();

            const username = $("#username").val();
            const password = $("#password").val();

            apiCall(
                `/hardware/${deviceId}/ssh-connect`,
                "POST",
                { username, password },
                (data) => {
                    if (data.success) {
                        showAlert("SSH connection established.", "success");
                        sshModal.hide();
                        executeRemoteCommands(data.commands);
                    } else {
                        showAlert("SSH connection failed. Check credentials.", "danger");
                    }
                },
                (xhr) => {
                    console.error("Error connecting via SSH:", xhr);
                    showAlert("Error connecting via SSH. Please try again.", "danger");
                }
            );
        });
    });

    // Execute remote commands on the device
    function executeRemoteCommands(commands) {
        commands.forEach((command) => {
            apiCall(
                "/hardware/execute-command",
                "POST",
                { command },
                (data) => {
                    if (data.success) {
                        console.log(`Command "${command}" executed successfully.`);
                    } else {
                        console.warn(`Command "${command}" failed: ${data.error}`);
                    }
                },
                (xhr) => {
                    console.error("Error executing command:", xhr);
                }
            );
        });
    }

    // Handle firmware upload
    firmwareForm.on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        apiCall(
            "/hardware/upload-firmware",
            "POST",
            Object.fromEntries(formData),
            (data) => {
                showAlert("Firmware uploaded successfully.", "success");
                fetchHardware();
            },
            (xhr) => {
                console.error("Error uploading firmware:", xhr);
                showAlert("Failed to upload firmware. Please try again.", "danger");
            }
        );
    });

    // Initial fetch
    fetchHardware();
});

$(document).ready(function () {
    // Utility function for API calls
    function apiCall(endpoint, method, data, onSuccess, onError) {
        const isPostMethod = method.toUpperCase() === "POST";

        $.ajax({
            url: endpoint,
            type: method,
            contentType: isPostMethod ? "application/json" : false,
            headers: {
                "X-CSRFToken": $("[name=csrf_token]").val(), // CSRF token from hidden input
            },
            data: isPostMethod ? JSON.stringify(data) : null, // Only stringify data for POST
            processData: false, // Prevent processing for non-POST
            success: function (response) {
                if (onSuccess) onSuccess(response);
            },
            error: function (xhr) {
                const errorMessage =
                    xhr.responseJSON?.error || "An error occurred while communicating with the server.";
                console.error(`API Error (${method} ${endpoint}):`, errorMessage);

                if (onError) {
                    onError(xhr);
                } else {
                    alert(errorMessage);
                }
            },
        });
    }

    // Fetch and display available blueprints
    function fetchBlueprints() {
        console.log("Fetching blueprints...");
        apiCall("/emulators/blueprints", "GET", null, (data) => {
            const blueprintList = $("#blueprint-list");
            const blueprintSelect = $("#blueprint-select");

            blueprintList.empty();
            blueprintSelect.empty().append('<option value="">Select Blueprint</option>');

            if (data.success && data.blueprints?.length > 0) {
                data.blueprints.forEach((blueprint) => {
                    const controller = blueprint.controller || {};
                    const peripherals = controller.peripherals || [];

                    // Add to the blueprint list
                    blueprintList.append(`
                            <li class="list-group-item">
                                <strong>${blueprint.name}</strong> - ${blueprint.description}
                                <button class="btn btn-sm btn-info preview-blueprint mt-2" data-blueprint="${blueprint.name}">Preview</button>
                                <ul class="mt-2">
                                    <li><strong>Controller:</strong> ${controller.name || "Not Specified"}</li>
                                    <li><strong>Connection Type:</strong> ${controller.connection?.type || "Not Specified"}</li>
                                    <li><strong>Peripherals:</strong></li>
                                    <ul>
                                        ${peripherals.map(peripheral => `
                                            <li>${peripheral.name} (${peripheral.type})</li>
                                        `).join("")}
                                    </ul>
                                </ul>
                            </li>
                        `);

                    // Add to the blueprint dropdown
                    blueprintSelect.append(`<option value="${blueprint.name}">${blueprint.name}</option>`);
                });
            } else {
                blueprintList.append('<li class="list-group-item text-center">No blueprints available.</li>');
            }
        });
    }

    // Fetch and display active emulations
    function fetchActiveEmulations() {
        console.log("Fetching active emulations...");
        apiCall("/emulators/list", "GET", null, (data) => {
            const emulationsList = $("#active-emulations-list");
            emulationsList.empty();

            if (data.success && data.emulations?.length > 0) {
                data.emulations.forEach((emulation) => {
                    emulationsList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            ${emulation.machine_name} (${emulation.blueprint})
                            <button class="btn btn-sm btn-danger stop-emulation" data-machine="${emulation.machine_name}">Stop</button>
                        </li>
                    `);
                });
            } else {
                emulationsList.append('<li class="list-group-item text-center">No active emulations.</li>');
            }
        });
    }

    // Fetch and display emulator logs
    function fetchLogs() {
        console.log("Fetching logs...");
        apiCall("/emulators/logs", "GET", null, (data) => {
            const logsContainer = $("#emulator-logs");
            logsContainer.empty();

            if (data.success && data.logs?.length > 0) {
                data.logs.forEach((log) => {
                    logsContainer.append(
                        `<div class="${log.type === "error" ? "text-danger" : "text-secondary"}">${log.message}</div>`
                    );
                });
            } else {
                logsContainer.append('<div class="text-center">No logs available.</div>');
            }
        });
    }

    // Start a new emulation
    $("#start-emulation-form").on("submit", function (event) {
        event.preventDefault();
        console.log("Starting emulation...");
        const machineName = $("#machine-name").val();
        const blueprint = $("#blueprint-select").val();
        const stressTest = $("#stress-test").is(":checked");

        if (!machineName || !blueprint) {
            alert("Please provide both a machine name and a blueprint.");
            return;
        }

        apiCall(
            "/emulators/start",
            "POST",
            { machine_name: machineName, blueprint, stress_test: stressTest },
            () => {
                alert("Emulation started successfully.");
                fetchActiveEmulations();
            }
        );
    });

    // Stop an active emulation
    $(document).on("click", ".stop-emulation", function () {
        const machineName = $(this).data("machine");
        console.log(`Stopping emulation for machine: ${machineName}`);

        apiCall(
            "/emulators/stop",
            "POST",
            { machine_name: machineName },
            () => {
                alert("Emulation stopped successfully.");
                fetchActiveEmulations();
            }
        );
    });

    // Before showing the modal
    const previewModal = new bootstrap.Modal(document.getElementById("preview-modal"));

    // Preview a blueprint
    $(document).on("click", ".preview-blueprint", function () {
        const blueprintName = $(this).data("blueprint");
        console.log(`Previewing blueprint: ${blueprintName}`);

        const modalBody = $("#preview-modal-body");

        modalBody.html(`<p>Loading preview for ${blueprintName}...</p>`);

        apiCall(`/emulators/preview/${blueprintName}`, "GET", null, (data) => {
            if (data.success) {
                const blueprint = data.blueprint || {};
                const controller = blueprint.controller || {};
                const peripherals = controller.peripherals || [];

                modalBody.html(`
                    <h5>${blueprint.name}</h5>
                    <p>${blueprint.description}</p>
                    <h6>Controller:</h6>
                    <ul>
                        <li><strong>Name:</strong> ${controller.name || "N/A"}</li>
                        <li><strong>Connection:</strong> ${JSON.stringify(controller.connection || {}, null, 2)}</li>
                    </ul>
                    <h6>Peripherals:</h6>
                    <ul>
                        ${peripherals.map(peripheral => `
                            <li>
                                <strong>${peripheral.name}</strong> (${peripheral.type})
                                <ul>
                                    <li><strong>Polling Frequency:</strong> ${peripheral.polling_frequency || "N/A"}</li>
                                    <li><strong>Read Command:</strong> ${peripheral.read_command || "N/A"}</li>
                                    <li><strong>Threshold:</strong> ${peripheral.threshold || "N/A"}</li>
                                </ul>
                            </li>
                        `).join("")}
                    </ul>
                `);
            } else {
                modalBody.html(`<p class="text-danger">Failed to load preview for ${blueprintName}.</p>`);
            }
        });

        previewModal.show();
    });

    // After the modal is hidden, ensure focus is removed
    $("#preview-modal").on("hidden.bs.modal", function () {
        $(this).find("*").blur(); // Remove focus from all elements inside the modal
    });


    // Add Emulator Form Submission
    $("#add-emulator-form").on("submit", async function (event) {
        event.preventDefault();
        console.log("Adding emulator...");

        const fileInput = $("#json-file")[0]?.files[0];
        const textInput = $("#json-text").val().trim();
        const nameOverride = $("#emulator-name").val().trim();
        const descriptionOverride = $("#emulator-description").val().trim();

        let configuration;

        try {
            // Load the JSON configuration from the file or text input
            if (fileInput) {
                const fileText = await fileInput.text();
                configuration = JSON.parse(fileText);
            } else if (textInput) {
                configuration = JSON.parse(textInput);
            } else {
                throw new Error("No file or JSON text provided.");
            }

            // Ensure the configuration has the necessary fields
            if (!configuration.id) throw new Error("Configuration must include an 'id' field.");
            if (!configuration.name) throw new Error("Configuration must include a 'name' field.");
            if (!configuration.description) throw new Error("Configuration must include a 'description' field.");

            // Override fields if provided in the form
            if (nameOverride) configuration.name = nameOverride;
            if (descriptionOverride) configuration.description = descriptionOverride;

            // Send the request to the API
            apiCall(
                "/emulators/add",
                "POST",
                { name: configuration.name, description: configuration.description, configuration },
                (response) => {
                    alert(response.message);
                    if (response.success) {
                        $("#add-emulator-modal").modal("hide");
                        fetchBlueprints();
                    }
                }
            );
        } catch (error) {
            console.error(error);
            alert("Error: " + error.message);
        }
    });


    /**
     * Validate the configuration JSON structure.
     * @param {Object} configuration - Parsed JSON object.
     * @throws Will throw an error if validation fails.
     */
    function validateConfiguration(configuration) {
        if (!configuration.id) throw new Error("Configuration must include an 'id' field.");
        if (!configuration.name) throw new Error("Configuration must include a 'name' field.");
        if (!configuration.type) throw new Error("Configuration must include a 'type' field.");
        if (!configuration.description) throw new Error("Configuration must include a 'description' field.");
        if (!configuration.protocol) throw new Error("Configuration must include a 'protocol' field.");
        if (!configuration.controller) throw new Error("Configuration must include a 'controller' field.");

        if (!configuration.controller) throw new Error("Configuration must include a 'controller' field.");
        if (!configuration.controller.name) throw new Error("Controller must include a 'name' field.");
        if (!configuration.controller.connection) throw new Error("Controller must include a 'connection' field.");
        if (!configuration.controller.peripherals || !Array.isArray(configuration.controller.peripherals)) {
            throw new Error("Controller must include a 'peripherals' array.");
        }

        // Validate each peripheral
        configuration.controller.peripherals.forEach((peripheral, index) => {
            if (!peripheral.name) throw new Error(`Peripheral ${index + 1} must include a 'name' field.`);
            if (!peripheral.type) throw new Error(`Peripheral ${index + 1} must include a 'type' field.`);
            if (!peripheral.connection) throw new Error(`Peripheral ${index + 1} must include a 'connection' field.`);
        });

        if (!configuration.commands || !Array.isArray(configuration.commands)) {
            throw new Error("Configuration must include a 'commands' array.");
        }

        // Validate each command
        configuration.commands.forEach((command, index) => {
            if (!command.name) throw new Error(`Command ${index + 1} must include a 'name' field.`);
            if (!command.description) throw new Error(`Command ${index + 1} must include a 'description' field.`);
        });

        console.log("Configuration validation passed.");
    }



    // Initial data load
    fetchBlueprints();
    fetchActiveEmulations();
    fetchLogs();
    setInterval(fetchLogs, 5000); // Update logs every 5 seconds
});

$(document).ready(function () {
    // Utility to show alerts for API responses
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    // Utility to validate form inputs
    function validateInputs(inputs) {
        for (const [key, value] of Object.entries(inputs)) {
            if (!value) {
                showAlert(`Please provide a valid ${key}.`, true);
                return false;
            }
        }
        return true;
    }

    // Fetch and display available blueprints
    function fetchBlueprints() {
        console.log("Fetching blueprints...");
        apiCall(
            "/emulators/blueprints",
            "GET",
            null,
            (data) => {
                const blueprintList = $("#blueprint-list");
                const blueprintSelect = $("#blueprint-select");

                blueprintList.empty();
                blueprintSelect.empty().append('<option value="">Select Blueprint</option>');

                if (data.success && data.blueprints?.length > 0) {
                    data.blueprints.forEach((blueprint) => {
                        const controller = blueprint.controller || {};
                        const peripherals = controller.peripherals || [];

                        // Dynamically add to the blueprint list
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

                        // Dynamically add to the blueprint select dropdown
                        blueprintSelect.append(`<option value="${blueprint.name}">${blueprint.name}</option>`);
                    });
                } else {
                    blueprintList.append('<li class="list-group-item text-center">No blueprints available.</li>');
                }
            },
            (xhr) => {
                // if we get an error in this specific spot it means the server is down or the API is broken
                // Be sure to also check the console for any database or server errors regarding tokens
                showAlert("Failed to fetch blueprints.", true);
                console.error("Blueprint fetch error:", xhr);
            }
        );
    }

    // Fetch and display active emulations
    function fetchActiveEmulations() {
        console.log("Fetching active emulations...");
        apiCall(
            "/emulators/list",
            "GET",
            null,
            (data) => {
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
            },
            (xhr) => {
                // If we get an error, it means the server is down or the API is broken
                showAlert("Failed to fetch active emulations.", true);
                console.error("Emulation fetch error:", xhr);
            }
        );
    }

    // Fetch and display emulator logs
    function fetchLogs() {
        console.log("Fetching logs...");
        apiCall(
            "/emulators/logs",
            "GET",
            null,
            (data) => {
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
            },
            (xhr) => {
                showAlert("Failed to fetch logs.", true);
                console.error("Logs fetch error:", xhr);
            }
        );
    }

    // Start a new emulation
    $("#start-emulation-form").on("submit", function (event) {
        event.preventDefault();
        console.log("Starting emulation...");

        const machineName = $("#machine-name").val();
        const blueprint = $("#blueprint-select").val();
        const stressTest = $("#stress-test").is(":checked");

        if (!validateInputs({ "Machine Name": machineName, Blueprint: blueprint })) return;

        apiCall(
            "/emulators/start",
            "POST",
            { machine_name: machineName, blueprint, stress_test: stressTest },
            () => {
                showAlert("Emulation started successfully.");
                fetchActiveEmulations();
            },
            (xhr) => {
                showAlert("Failed to start emulation.", true);
                console.error("Start emulation error:", xhr);
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
                showAlert("Emulation stopped successfully.");
                fetchActiveEmulations();
            },
            (xhr) => {
                showAlert("Failed to stop emulation.", true);
                console.error("Stop emulation error:", xhr);
            }
        );
    });

    // Preview a blueprint
    $(document).on("click", ".preview-blueprint", function () {
        const blueprintName = $(this).data("blueprint");
        console.log(`Previewing blueprint: ${blueprintName}`);

        const modalBody = $("#preview-modal-body");

        modalBody.html(`<p>Loading preview for ${blueprintName}...</p>`);

        apiCall(
            `/emulators/preview/${blueprintName}`,
            "GET",
            null,
            (data) => {
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
            },
            (xhr) => {
                modalBody.html(`<p class="text-danger">Error loading blueprint preview.</p>`);
                console.error("Blueprint preview error:", xhr);
            }
        );

        const previewModal = new bootstrap.Modal(document.getElementById("preview-modal"));
        previewModal.show();
    });

    const editorContainer = document.getElementById("json-editor");
    const jsonEditor = new JSONEditor(editorContainer, {
        mode: "tree",
        modes: ["tree", "code"],
        onError: function (err) {
            alert(`JSON Editor Error: ${err}`);
        },
    });

    // Utility: Show alerts for user feedback
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    // Utility: Resize JSON editor dynamically
    function resizeEditor() {
        const editorHeight = window.innerHeight * 0.6; // 60% of the viewport height
        editorContainer.style.height = `${editorHeight}px`;
    }

    // Handle JSON file upload
    $("#upload-json-file").on("change", function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                try {
                    const jsonData = JSON.parse(e.target.result);
                    jsonEditor.set(jsonData); // Populate editor
                    console.log("JSON loaded into editor:", jsonData);
                } catch (err) {
                    showAlert("Invalid JSON file. Please upload a valid JSON file.", true);
                }
            };
            reader.readAsText(file);
        }
    });

    // Save JSON changes and send to server
    $("#save-json-button").on("click", function () {
        try {
            const modifiedData = jsonEditor.get();
            const filename = prompt("Enter filename for the modified JSON:", "modified.json");
            if (filename) {
                apiCall(
                    "/emulators/json/save",
                    "POST",
                    { data: modifiedData, filename },
                    (response) => {
                        showAlert(response.message || "JSON saved successfully.");
                        console.log("Save response:", response);
                    },
                    (xhr) => {
                        showAlert("Failed to save JSON. Check console for details.", true);
                        console.error("Error saving JSON:", xhr);
                    }
                );
            }
        } catch (err) {
            showAlert("Invalid JSON. Please correct the structure and try again.", true);
        }
    });

    // Add Emulator Form Submission
    $("#add-emulator-form").on("submit", async function (event) {
        event.preventDefault();

        console.log("Adding emulator...");
        const fileInput = $("#json-file")[0]?.files[0];
        const textInput = $("#json-text").val().trim();
        const nameOverride = $("#emulator-name").val().trim();
        const descriptionOverride = $("#emulator-description").val().trim();

        if (!fileInput && !textInput) {
            showAlert("Please upload a JSON file or provide JSON text.", true);
            return;
        }

        let configuration;
        try {
            if (fileInput) {
                console.log("Reading JSON from file...");
                const fileText = await fileInput.text();
                configuration = JSON.parse(fileText);
            } else if (textInput) {
                console.log("Reading JSON from text input...");
                configuration = JSON.parse(textInput);
            }

            if (nameOverride) configuration.name = nameOverride;
            if (descriptionOverride) configuration.description = descriptionOverride;

            validateConfiguration(configuration);

            apiCall(
                "/emulators/add",
                "POST",
                { name: configuration.name, description: configuration.description, configuration },
                (response) => {
                    showAlert(response.message || "Emulator added successfully.");
                    $("#add-emulator-modal").modal("hide");
                    fetchBlueprints(); // Refresh list
                },
                (xhr) => {
                    showAlert("Failed to add emulator.", true);
                    console.error("Add emulator error:", xhr);
                }
            );
        } catch (error) {
            console.error("Error parsing configuration:", error);
            showAlert("Error processing the JSON file or input. Check console for details.", true);
        }
    });

    // JSON Validation Function
    function validateConfiguration(configuration) {
        if (!configuration.name) throw new Error("Configuration must include a 'name' field.");
        if (!configuration.type) throw new Error("Configuration must include a 'type' field.");
        if (!configuration.description) throw new Error("Configuration must include a 'description' field.");
        if (!configuration.protocol) throw new Error("Configuration must include a 'protocol' field.");
        if (!configuration.controller) throw new Error("Configuration must include a 'controller' field.");
        if (!configuration.controller.name) throw new Error("Controller must include a 'name' field.");
        if (!configuration.controller.connection) throw new Error("Controller must include a 'connection' field.");
        if (!configuration.controller.peripherals || !Array.isArray(configuration.controller.peripherals)) {
            throw new Error("Controller must include a 'peripherals' array.");
        }

        configuration.controller.peripherals.forEach((peripheral, index) => {
            if (!peripheral.name) throw new Error(`Peripheral ${index + 1} must include a 'name' field.`);
            if (!peripheral.type) throw new Error(`Peripheral ${index + 1} must include a 'type' field.`);
            if (!peripheral.connection) throw new Error(`Peripheral ${index + 1} must include a 'connection' field.`);
        });

        if (!configuration.commands || !Array.isArray(configuration.commands)) {
            throw new Error("Configuration must include a 'commands' array.");
        }

        configuration.commands.forEach((command, index) => {
            if (!command.name) throw new Error(`Command ${index + 1} must include a 'name' field.`);
            if (!command.description) throw new Error(`Command ${index + 1} must include a 'description' field.`);
        });

        console.log("Configuration validation passed.");
    }

    // Adjust JSON Editor size dynamically
    resizeEditor();
    $(window).on("resize", resizeEditor);

    // Initial data load
    fetchBlueprints();
    fetchActiveEmulations();
    fetchLogs();
    setInterval(fetchLogs, 5000); // Update logs every 5 seconds
});

$(document).ready(function () {
    // Utility to show alerts for API responses
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    // Utility: Validate form inputs
    function validateInputs(inputs) {
        for (const [key, value] of Object.entries(inputs)) {
            if (!value) {
                showAlert(`Please provide a valid ${key}.`, true);
                return false;
            }
        }
        return true;
    }

    // Fetch configuration from the database
    async function fetchConfigurationFromDatabase(blueprintName) {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

            const response = await fetch(`/configurations/api/${unquote(blueprintName)}`, {
                method: "GET",
                headers: { "X-CSRFToken": csrfToken },
            });

            if (!response.ok) {
                console.warn(`Configuration for "${blueprintName}" not found.`);
                return null;
            }

            const data = await response.json();
            return data.success ? data.configuration : null;
        } catch (error) {
            console.error("Error fetching configuration:", error);
            return null;
        }
    }

    // Start emulation
    function startEmulation(configuration) {
        apiCall(
            "/emulators/start",
            "POST",
            configuration,
            (response) => {
                showAlert("Emulation started successfully!", false);
                fetchActiveEmulations(); // Refresh the active emulations list
            },
            (xhr) => {
                showAlert("Failed to start emulation.", true);
                console.error("Start emulation error:", xhr);
            }
        );
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

    // Unified handler for starting emulations
    $("#start-emulation-form").on("submit", async function (event) {
        event.preventDefault();
        console.log("Starting emulation...");

        const machineName = $("#machine-name").val();
        const blueprintName = $("#blueprint-select").val();
        const stressTest = $("#stress-test").is(":checked");

        if (!validateInputs({ "Machine Name": machineName, Blueprint: blueprintName })) return;

        try {
            // Step 1: Fetch configuration from the database
            const configuration = await fetchConfigurationFromDatabase(blueprintName);

            if (configuration) {
                // Step 2: Validate and start emulation if configuration exists
                validateConfiguration(configuration, { warnOnly: true });
                startEmulation({ ...configuration, machine_name: machineName, stress_test: stressTest });
            } else {
                // Step 3: Prompt user to create a new configuration if none exists
                showAlert(`No configuration found for "${blueprintName}". Please create one.`, true);
                jsonEditor.set({ type: "blueprint", name: blueprintName, description: "" });
                $("#json-editor-container").removeClass("d-none");
                showAlert("Start creating your configuration in the JSON editor.");
            }
        } catch (error) {
            console.error("Error during emulation setup:", error);
            showAlert("An error occurred while starting the emulation.", true);
        }
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
                showAlert("Emulation stopped successfully.", false);
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
        onChangeJSON: function (json) {
            console.log("Updated JSON:", json);
        },
    });

    function openDynamicFieldEditor(fields) {
        jsonEditor.set(fields);
        $("#dynamic-field-editor-modal").modal("show");
    }

    $("#save-dynamic-fields").on("click", function () {
        const updatedConfiguration = jsonEditor.get();
        validateConfiguration(updatedConfiguration, { warnOnly: false });
        console.log("Dynamic fields saved:", updatedConfiguration);
        $("#dynamic-field-editor-modal").modal("hide");
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

    function validateConfiguration(configuration, options = { warnOnly: true }) {
        const warnings = [];
        const errors = [];

        // Validate top-level fields and allow dynamic types
        if (!configuration.type) {
            errors.push("Configuration must include a 'type' field.");
        } else {
            console.log(`Validating configuration type: ${configuration.type}`);
        }

        // Allow missing name and description but warn the user
        if (!configuration.name) warnings.push("Configuration is missing a 'name' field.");
        if (!configuration.description) warnings.push("Configuration is missing a 'description' field.");

        // Validate based on the type
        switch (configuration.type) {
            case "blueprint":
                validateBlueprint(configuration, warnings, errors);
                break;
            case "controller":
                validateController(configuration, warnings, errors);
                break;
            case "peripheral":
                validatePeripheral(configuration, warnings, errors);
                break;
            case "emulator":
                validateEmulator(configuration, warnings, errors);
                break;
            default:
                warnings.push(`Unknown configuration type: ${configuration.type}. You can define it dynamically.`);
                break;
        }

        // Display warnings and errors
        if (warnings.length > 0) {
            console.warn("Validation Warnings:", warnings);
        }

        if (errors.length > 0) {
            throw new Error(`Validation Errors: ${errors.join(", ")}`);
        }

        console.log("Validation completed successfully.");
    }

    // Allow users to define missing fields dynamically
    function validateBlueprint(configuration, warnings, errors) {
        if (!configuration.blueprint) {
            warnings.push("Blueprint is missing a 'blueprint' field.");
            return;
        }

        const requiredFields = ["controllers", "peripherals"];
        handleDynamicFields(configuration.blueprint, requiredFields, warnings);
    }

    function validateController(controller, warnings, errors) {
        const requiredFields = ["name", "connection"];
        handleDynamicFields(controller, requiredFields, warnings);
    }

    function validatePeripheral(peripheral, warnings, errors) {
        const requiredFields = ["name", "type", "connection"];
        handleDynamicFields(peripheral, requiredFields, warnings);
    }

    function validateEmulator(emulator, warnings, errors) {
        const requiredFields = ["firmware", "hardwareAbstractionLayer", "supportedPeripherals"];
        handleDynamicFields(emulator, requiredFields, warnings);
    }

    // Handle dynamic field validation
    function handleDynamicFields(object, requiredFields, warnings) {
        requiredFields.forEach((field) => {
            if (!object[field]) {
                warnings.push(`Field '${field}' is missing. It can be added dynamically.`);
            }
        });

        // Check for additional fields not defined
        Object.keys(object).forEach((key) => {
            if (!requiredFields.includes(key)) {
                warnings.push(`Field '${key}' is not recognized but will be allowed.`);
            }
        });
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

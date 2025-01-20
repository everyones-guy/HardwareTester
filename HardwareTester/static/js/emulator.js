$(document).ready(function () {
    // Utility function for API calls
    function apiCall(endpoint, method, data, onSuccess, onError) {
        $.ajax({
            url: endpoint,
            type: method,
            contentType: method === "POST" ? "application/json" : undefined,
            data: method === "POST" ? JSON.stringify(data) : data,
            processData: method !== "POST",
            success: onSuccess,
            error: function (xhr) {
                const errorMessage = xhr.responseJSON?.message || "An error occurred while communicating with the server.";
                console.error(`API Error (${method} ${endpoint}):`, errorMessage);
                if (onError) onError(xhr);
                else alert(errorMessage);
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

            if (data.success && data.blueprints.length > 0) {
                data.blueprints.forEach((blueprint) => {
                    blueprintList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            ${blueprint.name}
                            <button class="btn btn-sm btn-info preview-blueprint" data-blueprint="${blueprint.name}">Preview</button>
                        </li>
                    `);
                    blueprintSelect.append(`<option value="${blueprint.name}">${blueprint.name}</option>`);
                });
            } else {
                blueprintList.append('<li class="list-group-item text-center">No blueprints available.</li>');
            }
        }, () => alert("Failed to fetch blueprints."));
    }

    // Fetch and display active emulations
    function fetchActiveEmulations() {
        console.log("Fetching active emulations...");
        apiCall("/emulators/list", "GET", null, (data) => {
            const emulationsList = $("#active-emulations-list");
            emulationsList.empty();

            if (data.success && data.emulations.length > 0) {
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
        }, () => alert("Failed to fetch active emulations."));
    }

    // Fetch and display emulator logs
    function fetchLogs() {
        console.log("Fetching logs...");
        apiCall("/emulators/logs", "GET", null, (data) => {
            const logsContainer = $("#emulator-logs");
            logsContainer.empty();

            if (data.success && data.logs.length > 0) {
                data.logs.forEach((log) => {
                    logsContainer.append(`<div class="${log.type === "error" ? "text-danger" : "text-secondary"}">${log.message}</div>`);
                });
            } else {
                logsContainer.append('<div class="text-center">No logs available.</div>');
            }
        }, () => alert("Failed to fetch logs."));
    }

    // Upload a new blueprint
    $("#blueprint-upload-form").on("submit", function (event) {
        event.preventDefault();
        console.log("Uploading blueprint...");
        const formData = new FormData(this);

        $.ajax({
            url: "/emulators/load-blueprint",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function () {
                alert("Blueprint uploaded successfully.");
                fetchBlueprints();
            },
            error: () => alert("Failed to upload blueprint."),
        });
    });

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
            },
            () => alert("Failed to start emulation.")
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
            },
            () => alert("Failed to stop emulation.")
        );
    });

    // Preview a blueprint
    $(document).on("click", ".preview-blueprint", function () {
        const blueprintName = $(this).data("blueprint");
        console.log(`Previewing blueprint: ${blueprintName}`);
        const previewModal = new bootstrap.Modal(document.getElementById("preview-modal"));
        const modalBody = $("#preview-modal-body");

        modalBody.html(`<p>Loading preview for ${blueprintName}...</p>`);

        apiCall(
            `/emulators/preview/${blueprintName}`,
            "GET",
            null,
            (data) => {
                if (data.success) {
                    modalBody.html(`<img src="${data.preview_url}" alt="${blueprintName}" class="img-fluid">`);
                } else {
                    modalBody.html(`<p class="text-danger">Failed to load preview for ${blueprintName}.</p>`);
                }
            },
            () => modalBody.html(`<p class="text-danger">An error occurred while fetching the preview.</p>`)
        );

        previewModal.show();
    });

    // Initialize Add Emulator Form
    function initializeEmulatorForm() {
        $("#add-emulator-modal").on("show.bs.modal", function () {
            $("#json-file").val(null);
            $("#json-text").val("");
        });

        $("#add-emulator-form").off("submit").on("submit", async function (event) {
            event.preventDefault();
            console.log("Adding emulator...");
            const fileInput = $("#json-file")[0]?.files[0];
            const textInput = $("#json-text").val().trim();
            let jsonData;

            try {
                if (fileInput) {
                    const fileText = await fileInput.text();
                    jsonData = JSON.parse(fileText);
                } else if (textInput) {
                    jsonData = JSON.parse(textInput);
                } else {
                    throw new Error("No input provided.");
                }
            } catch (error) {
                alert("Invalid JSON. Please correct the input.");
                return;
            }

            apiCall(
                "/api/add-emulator",
                "POST",
                jsonData,
                (response) => {
                    alert(response.message);
                    if (response.success) {
                        $("#add-emulator-modal").modal("hide");
                        fetchActiveEmulations();
                    }
                },
                () => alert("Failed to add emulator.")
            );
        });
    }

    window.initializeEmulatorForm = initializeEmulatorForm;

    // Initial data load
    fetchBlueprints();
    fetchActiveEmulations();
    fetchLogs();
    setInterval(fetchLogs, 5000); // Update logs every 5 seconds
});

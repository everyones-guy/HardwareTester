
$(document).ready(function () {
    // Fetch blueprints
    function fetchBlueprints() {
        $.get("/emulator/blueprints", function (data) {
            const blueprintList = $("#blueprint-list");
            const blueprintSelect = $("#blueprint-select");
            blueprintList.empty();
            blueprintSelect.empty().append('<option value="">Select Blueprint</option>');

            if (data.success) {
                data.blueprints.forEach((blueprint) => {
                    blueprintList.append(`<li class="list-group-item">${blueprint}</li>`);
                    blueprintSelect.append(`<option value="${blueprint}">${blueprint}</option>`);
                });
            } else {
                blueprintList.append('<li class="list-group-item">No blueprints available.</li>');
            }
        });
    }

    // Fetch active emulations
    function fetchActiveEmulations() {
        $.get("/emulator/list", function (data) {
            const emulationsList = $("#active-emulations-list");
            emulationsList.empty();

            if (data.success) {
                data.emulations.forEach((emulation) => {
                    emulationsList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            ${emulation.machine_name} (${emulation.blueprint})
                            <button class="btn btn-danger btn-sm stop-emulation" data-machine="${emulation.machine_name}">
                                Stop
                            </button>
                        </li>
                    `);
                });
            } else {
                emulationsList.append('<li class="list-group-item">No active emulations.</li>');
            }
        });
    }

    // Fetch emulator logs
    function fetchLogs() {
        $.get("/emulator/logs", function (data) {
            const logsContainer = $("#emulator-logs");
            logsContainer.empty();

            if (data.success) {
                data.logs.forEach((log) => {
                    logsContainer.append(`<div>${log}</div>`);
                });
            } else {
                logsContainer.append('<div>No logs available.</div>');
            }
        });
    }

    // Handle blueprint upload
    $("#blueprint-upload-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        $.ajax({
            url: "/emulator/load-blueprint",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function () {
                alert("Blueprint uploaded successfully.");
                fetchBlueprints();
            },
            error: function () {
                alert("Failed to upload blueprint.");
            }
        });
    });

    // Handle starting a new emulation
    $("#start-emulation-form").on("submit", function (event) {
        event.preventDefault();
        const machineName = $("#machine-name").val();
        const blueprint = $("#blueprint-select").val();
        const stressTest = $("#stress-test").is(":checked");

        $.ajax({
            url: "/emulator/start",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ machine_name: machineName, blueprint, stress_test: stressTest }),
            success: function () {
                alert("Emulation started successfully.");
                fetchActiveEmulations();
            },
            error: function () {
                alert("Failed to start emulation.");
            }
        });
    });

    // Handle stopping an emulation
    $(document).on("click", ".stop-emulation", function () {
        const machineName = $(this).data("machine");

        $.ajax({
            url: "/emulator/stop",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ machine_name: machineName }),
            success: function () {
                alert("Emulation stopped successfully.");
                fetchActiveEmulations();
            },
            error: function () {
                alert("Failed to stop emulation.");
            }
        });
    });

    // Initialize
    fetchBlueprints();
    fetchActiveEmulations();
    fetchLogs();
    setInterval(fetchLogs, 5000); // Update logs every 5 seconds
});



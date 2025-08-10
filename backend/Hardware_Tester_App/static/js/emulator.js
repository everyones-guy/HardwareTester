$(document).ready(function () {
    /**
     * Utility: Show alerts for API responses
     */
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    /**
     * Validate form inputs before submission
     */
    function validateInputs(inputs) {
        for (const [key, value] of Object.entries(inputs)) {
            if (!value) {
                showAlert(`Please provide a valid ${key}.`, true);
                return false;
            }
        }
        return true;
    }

    /**
     * Fetch and display available blueprints
     */
    async function fetchBlueprints() {
        console.log("Fetching blueprints...");
        try {
            const data = await apiCall("/emulators/blueprints", "GET");

            const blueprintList = $("#blueprint-list");
            const blueprintSelect = $("#blueprint-select");

            blueprintList.empty();
            blueprintSelect.empty().append('<option value="">Select Blueprint</option>');

            if (data.success && data.blueprints?.length > 0) {
                data.blueprints.forEach((blueprint) => {
                    const controller = blueprint.controller || {};
                    const peripherals = controller.peripherals || [];

                    blueprintList.append(`
                        <li class="list-group-item">
                            <strong>${blueprint.name}</strong> - ${blueprint.description}
                            <button class="btn btn-sm btn-info preview-blueprint mt-2" data-blueprint="${blueprint.name}">Preview</button>
                            <ul class="mt-2">
                                <li><strong>Controller:</strong> ${controller.name || "Not Specified"}</li>
                                <li><strong>Connection Type:</strong> ${controller.connection?.type || "Not Specified"}</li>
                                <li><strong>Peripherals:</strong></li>
                                <ul>
                                    ${peripherals.map(peripheral => `<li>${peripheral.name} (${peripheral.type})</li>`).join("")}
                                </ul>
                            </ul>
                        </li>
                    `);

                    blueprintSelect.append(`<option value="${blueprint.name}">${blueprint.name}</option>`);
                });
            } else {
                blueprintList.append('<li class="list-group-item text-center">No blueprints available.</li>');
            }
        } catch (error) {
            showAlert("Failed to fetch blueprints.", true);
            console.error("Blueprint fetch error:", error);
        }
    }

    /**
     * Fetch and display active emulations
     */
    async function fetchActiveEmulations() {
        console.log("Fetching active emulations...");
        try {
            const data = await apiCall("/emulators/list", "GET");

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
        } catch (error) {
            showAlert("Failed to fetch active emulations.", true);
            console.error("Emulation fetch error:", error);
        }
    }

    /**
     * Start emulation with selected blueprint
     */
    $("#start-emulation-form").on("submit", async function (event) {
        event.preventDefault();
        console.log("Starting emulation...");

        const machineName = $("#machine-name").val();
        const blueprintName = $("#blueprint-select").val();
        const stressTest = $("#stress-test").is(":checked");

        if (!validateInputs({ "Machine Name": machineName, Blueprint: blueprintName })) return;

        try {
            const configuration = await apiCall(`/emulators/load-blueprint/${encodeURIComponent(blueprintName)}`, "GET");

            if (configuration.success) {
                await apiCall("/emulators/start", "POST", { ...configuration.data, machine_name: machineName, stress_test: stressTest });
                showAlert("Emulation started successfully!");
                fetchActiveEmulations();
            } else {
                showAlert(`No configuration found for "${blueprintName}". Please create one.`, true);
            }
        } catch (error) {
            showAlert("An error occurred while starting the emulation.", true);
            console.error("Start emulation error:", error);
        }
    });

    /**
     * Stop an active emulation
     */
    $(document).on("click", ".stop-emulation", async function () {
        const machineName = $(this).data("machine");
        console.log(`Stopping emulation for machine: ${machineName}`);

        try {
            await apiCall("/emulators/stop", "POST", { machine_name: machineName });
            showAlert("Emulation stopped successfully.");
            fetchActiveEmulations();
        } catch (error) {
            showAlert("Failed to stop emulation.", true);
            console.error("Stop emulation error:", error);
        }
    });

    /**
     * Preview a blueprint
     */
    $(document).on("click", ".preview-blueprint", async function () {
        const blueprintName = $(this).data("blueprint");
        console.log(`Previewing blueprint: ${blueprintName}`);

        const modalBody = $("#preview-modal-body");
        modalBody.html(`<p>Loading preview for ${blueprintName}...</p>`);

        try {
            const data = await apiCall(`/emulators/preview/${blueprintName}`, "GET");

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
                            <li><strong>${peripheral.name}</strong> (${peripheral.type})</li>
                        `).join("")}
                    </ul>
                `);
            } else {
                modalBody.html(`<p class="text-danger">Failed to load preview for ${blueprintName}.</p>`);
            }
        } catch (error) {
            modalBody.html(`<p class="text-danger">Error loading blueprint preview.</p>`);
            console.error("Blueprint preview error:", error);
        }

        new bootstrap.Modal(document.getElementById("preview-modal")).show();
    });

    /**
     * Initialize emulator functionalities
     */
    fetchBlueprints();
    fetchActiveEmulations();
});

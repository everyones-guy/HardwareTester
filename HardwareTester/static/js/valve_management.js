$(document).ready(function () {
    const valveList = $("#valve-list");

    // Fetch and display valves
    function fetchValves() {
        apiCall("/valves/list", "GET", null, (data) => {
            valveList.empty();

            if (data.success) {
                if (data.valves.length > 0) {
                    data.valves.forEach((valve) => {
                        valveList.append(`
                            <li class="list-group-item">
                                <strong>${valve.name}</strong> (${valve.type}) - State: <span class="valve-state">${valve.state || "Unknown"}</span>
                                <button class="btn btn-secondary btn-sm float-end change-state-btn me-2" data-id="${valve.id}">Change State</button>
                                <button class="btn btn-danger btn-sm float-end delete-valve-btn" data-id="${valve.id}">Delete</button>
                            </li>
                        `);
                    });
                } else {
                    valveList.append("<li class='list-group-item'>No valves found.</li>");
                }
            } else {
                showAlert(`Error fetching valves: ${data.error}`, "danger");
            }
        }, (xhr) => {
            showAlert("Failed to fetch valves. Please try again later.", "danger");
            console.error(xhr.responseText);
        });
    }

    // Add a new valve
    $("#add-valve-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        apiCall("/valves/add", "POST", Object.fromEntries(formData), (response) => {
            showAlert(response.message, "success");
            fetchValves();
        }, (xhr) => {
            showAlert("Failed to add valve. Please try again later.", "danger");
            console.error(xhr.responseText);
        });
    });

    // Delete a valve
    valveList.on("click", ".delete-valve-btn", function () {
        const valveId = $(this).data("id");

        apiCall(`/valves/${valveId}/delete`, "DELETE", null, (response) => {
            showAlert(response.message, "success");
            fetchValves();
        }, (xhr) => {
            showAlert("Failed to delete valve. Please try again later.", "danger");
            console.error(xhr.responseText);
        });
    });

    // Change the state of a valve
    valveList.on("click", ".change-state-btn", function () {
        const valveId = $(this).data("id");
        const newState = prompt("Enter new state (open, closed, faulty, maintenance):");

        if (newState) {
            apiCall(`/valves/${valveId}/change-state`, "POST", { state: newState }, (response) => {
                showAlert(`Valve state updated to ${newState}.`, "success");
                fetchValves();
            }, (xhr) => {
                showAlert("Failed to change valve state. Please try again later.", "danger");
                console.error(xhr.responseText);
            });
        } else {
            showAlert("State update canceled. Please provide a valid state.", "warning");
        }
    });

    // Update a valve
    valveList.on("click", ".update-valve-btn", function () {
        const valveId = $(this).data("id");
        const newName = prompt("Enter new name for the valve:");
        const newType = prompt("Enter new type for the valve:");
        const newSpecs = prompt("Enter new specifications for the valve:");

        if (newName && newType && newSpecs) {
            const data = { name: newName, type: newType, specifications: newSpecs };

            apiCall(`/valves/${valveId}/update`, "PUT", data, (response) => {
                showAlert(response.message, "success");
                fetchValves();
            }, (xhr) => {
                showAlert("Failed to update valve. Please try again later.", "danger");
                console.error(xhr.responseText);
            });
        } else {
            showAlert("Update canceled. All fields are required.", "warning");
        }
    });

    // Initial fetch to load valves
    fetchValves();
});

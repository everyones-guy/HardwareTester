$(document).ready(function () {
    const valveList = $("#valve-list");
    const addValveBtn = $("#add-valve-btn");

    // Fetch and display valves
    function fetchValves() {
        $.ajax({
            url: "/valves/list",
            method: "GET",
            success: function (data) {
                if (data.success) {
                    valveList.empty();
                    if (data.valves.length > 0) {
                        data.valves.forEach(valve => {
                            const valveItem = `
                                <li class="list-group-item">
                                    <strong>${valve.name}</strong> (${valve.type}) - State: <span class="valve-state">${valve.state || "Unknown"}</span>
                                    <button class="btn btn-secondary btn-sm float-end change-state-btn me-2" data-id="${valve.id}">Change State</button>
                                    <button class="btn btn-danger btn-sm float-end delete-valve-btn" data-id="${valve.id}">Delete</button>
                                </li>`;
                            valveList.append(valveItem);
                        });
                    } else {
                        valveList.append("<li class='list-group-item'>No valves found.</li>");
                    }
                } else {
                    alert(`Error fetching valves: ${data.error}`);
                }
            },
            error: function (xhr) {
                alert("Failed to fetch valves. Please try again later.");
                console.error(xhr.responseText);
            }
        });
    }

    // Add a new valve
    addValveBtn.on("click", function () {
        const name = prompt("Enter valve name:");
        const type = prompt("Enter valve type:");
        const specifications = prompt("Enter valve specifications:");

        if (name && type) {
            $.ajax({
                url: "/valves/add",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({ name, type, specifications }),
                success: function (data) {
                    if (data.success) {
                        alert("Valve added successfully.");
                        fetchValves();
                    } else {
                        alert(`Error adding valve: ${data.error}`);
                    }
                },
                error: function (xhr) {
                    alert("Failed to add valve. Please try again later.");
                    console.error(xhr.responseText);
                }
            });
        }
    });

    // Delete a valve
    valveList.on("click", ".delete-valve-btn", function () {
        const valveId = $(this).data("id");
        $.ajax({
            url: `/valves/${valveId}/delete`,
            method: "DELETE",
            success: function (data) {
                if (data.success) {
                    alert("Valve deleted successfully.");
                    fetchValves();
                } else {
                    alert(`Error deleting valve: ${data.error}`);
                }
            },
            error: function (xhr) {
                alert("Failed to delete valve. Please try again later.");
                console.error(xhr.responseText);
            }
        });
    });

    // Change the state of a valve
    valveList.on("click", ".change-state-btn", function () {
        const valveId = $(this).data("id");
        const newState = prompt("Enter new state (open, closed, faulty, maintenance):");

        if (newState) {
            $.ajax({
                url: `/valves/${valveId}/change-state`,
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({ state: newState }),
                success: function (data) {
                    if (data.success) {
                        alert(`Valve state updated to ${newState}.`);
                        fetchValves();
                    } else {
                        alert(`Error changing state: ${data.error}`);
                    }
                },
                error: function (xhr) {
                    alert("Failed to change valve state. Please try again later.");
                    console.error(xhr.responseText);
                }
            });
        }
    });

    // Initial fetch to load valves
    fetchValves();
});

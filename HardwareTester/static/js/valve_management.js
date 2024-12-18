$(document).ready(function () {
    // Function to update the list of valves
    function updateValveList() {
        $.get("/get-valves", function (data) {
            if (data.success) {
                const valves = data.valves;
                const list = $("#valve-list");
                list.empty();

                if (valves.length > 0) {
                    valves.forEach((valve) => {
                        list.append(
                            `<li class="list-group-item">
                                <strong>${valve.name}</strong> - ${valve.type}
                                <span class="badge bg-info float-end">ID: ${valve.id}</span>
                            </li>`
                        );
                    });
                } else {
                    list.append('<li class="list-group-item">No valves found.</li>');
                }
            } else {
                $("#valve-list").html(
                    `<li class="list-group-item text-danger">${data.message}</li>`
                );
            }
        });
    }

    // Function to refresh valve status
    function refreshValveStatus() {
        $.get("/get-valve-status", function (data) {
            if (data.success) {
                const statuses = data.statuses;
                const container = $("#valve-status-container");
                container.empty();

                statuses.forEach((status) => {
                    container.append(
                        `<div>
                            <strong>Valve ${status.id}</strong>: ${status.status}
                            <small class="text-muted">(Last updated: ${status.last_updated})</small>
                        </div>`
                    );
                });
            } else {
                $("#valve-status-container").html(
                    `<div class="text-danger">${data.message}</div>`
                );
            }
        });
    }

    // Call the update functions on page load
    updateValveList();
    refreshValveStatus();

    // Handle spec sheet upload form submission
    $("#upload-spec-sheet-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        $.ajax({
            url: "/upload-spec-sheet",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                $("#upload-spec-sheet-results").html(
                    `<div class="alert alert-success">${response.message}</div>`
                );
                updateValveList(); // Refresh the valve list
            },
            error: function (xhr) {
                const errorMessage = xhr.responseJSON?.message || "An error occurred";
                $("#upload-spec-sheet-results").html(
                    `<div class="alert alert-danger">${errorMessage}</div>`
                );
            },
        });
    });

    // Refresh valve status button click
    $("#refresh-valve-status").click(function () {
        refreshValveStatus();
    });
});

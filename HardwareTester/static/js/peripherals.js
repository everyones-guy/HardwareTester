$(document).ready(function () {
    const peripheralsList = $("#peripherals-list");
    const peripheralPreview = $("#peripheral-preview");
    const previewName = $("#preview-name");
    const previewProperties = $("#preview-properties");
    const addPeripheralForm = $("#add-peripheral-form");

    // Fetch peripherals and populate the list
    function fetchPeripherals() {
        $.ajax({
            url: "/peripherals/list",
            method: "GET",
            success: function (data) {
                peripheralsList.empty(); // Clear the list
                if (data.success) {
                    data.peripherals.forEach(function (peripheral) {
                        const listItem = `
                            <li class="list-group-item d-flex justify-content-between">
                                <span>${peripheral.name}</span>
                                <button class="btn btn-info btn-sm preview-peripheral" data-id="${peripheral.id}" data-properties='${JSON.stringify(peripheral.properties)}'>Preview</button>
                            </li>`;
                        peripheralsList.append(listItem);
                    });
                } else {
                    peripheralsList.html("<li class='list-group-item'>No peripherals found.</li>");
                }
            },
            error: function (xhr) {
                console.error("Error fetching peripherals:", xhr);
            },
        });
    }

    // Show peripheral preview
    $(document).on("click", ".preview-peripheral", function () {
        const peripheralId = $(this).data("id");
        const peripheralProperties = $(this).data("properties");

        previewName.text(peripheralId);
        previewProperties.text(JSON.stringify(peripheralProperties, null, 2));
        peripheralPreview.removeClass("d-none");

        // Add event listener for test connection
        $("#test-connection").off("click").on("click", function () {
            testPeripheralConnection(peripheralId);
        });

        // Add event listener for test device
        $("#test-device").off("click").on("click", function () {
            redirectToDashboard(peripheralId);
        });
    });

    // Test connection
    function testPeripheralConnection(peripheralId) {
        $.ajax({
            url: `/peripherals/test-connection/${peripheralId}`,
            method: "GET",
            success: function (data) {
                alert(data.message || "Connection test successful.");
            },
            error: function () {
                alert("Failed to test connection.");
            },
        });
    }

    // Redirect to dashboard
    function redirectToDashboard(peripheralId) {
        window.location.href = `/dashboard?peripheral_id=${peripheralId}`;
    }

    // Add peripheral form submission
    addPeripheralForm.on("submit", function (event) {
        event.preventDefault();

        const name = $("#peripheral-name").val();
        const properties = $("#peripheral-properties").val();

        $.ajax({
            url: "/peripherals/add",
            method: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": $("meta[name='csrf-token']").attr("content"),
            },
            data: JSON.stringify({ name, properties: JSON.parse(properties) }),
            success: function (data) {
                alert(data.message || "Peripheral added successfully.");
                fetchPeripherals();
                addPeripheralForm[0].reset();
            },
            error: function (xhr) {
                alert("Failed to add peripheral.");
                console.error(xhr);
            },
        });
    });

    // Initial fetch
    fetchPeripherals();
});

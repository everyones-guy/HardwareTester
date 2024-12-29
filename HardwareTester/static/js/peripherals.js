
// Fetch and display peripherals
function fetchPeripherals() {
    $.get("/peripherals/list", function (data) {
        const list = $("#peripherals-list");
        list.empty();

        if (data.success) {
            data.peripherals.forEach(peripheral => {
                const listItem = `
                    <li class="list-group-item">
                        <strong>${peripheral.name}</strong> 
                        <button class="btn btn-danger btn-sm float-end" onclick="deletePeripheral(${peripheral.id})">Delete</button>
                        <pre>${JSON.stringify(peripheral.properties, null, 2)}</pre>
                    </li>
                `;
                list.append(listItem);
            });
        } else {
            alert(data.error);
        }
    });
}

// Add a new peripheral
$("#add-peripheral-form").on("submit", function (event) {
    event.preventDefault();
    const name = $("#peripheral-name").val();
    const properties = JSON.parse($("#peripheral-properties").val());

    $.post("/peripherals/add", JSON.stringify({ name, properties }), function (data) {
        if (data.success) {
            alert(data.message);
            fetchPeripherals();
        } else {
            alert(data.error);
        }
    });
});

// Delete a peripheral
function deletePeripheral(peripheralId) {
    $.ajax({
        url: `/peripherals/delete/${peripheralId}`,
        type: "DELETE",
        headers: {
            "X-CSRFToken": $('meta[name="csrf-token"]').attr('content')  // Ensure CSRF token is sent
        },
        success: function (data) {
            if (data.success) {
                alert(data.message);
                fetchPeripherals();
            } else {
                alert(data.error);
            }
        }
    });
}

// Fetch peripherals on page load
$(document).ready(function () {
    fetchPeripherals();
});


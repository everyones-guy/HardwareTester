document.addEventListener("DOMContentLoaded", () => {
    const peripheralsList = document.getElementById("peripherals-list");
    const peripheralPreview = document.getElementById("peripheral-preview");
    const previewName = document.getElementById("preview-name");
    const previewProperties = document.getElementById("preview-properties");
    const addPeripheralForm = document.getElementById("add-peripheral-form");

    // Fetch peripherals and populate the list
    function fetchPeripherals() {
        fetch("/peripherals/list")
            .then(response => response.json())
            .then(data => {
                peripheralsList.innerHTML = ""; // Clear the list
                if (data.success) {
                    data.peripherals.forEach(peripheral => {
                        const listItem = document.createElement("li");
                        listItem.classList.add("list-group-item", "d-flex", "justify-content-between");
                        listItem.innerHTML = `
                            <span>${peripheral.name}</span>
                            <button class="btn btn-info btn-sm" data-id="${peripheral.id}">Preview</button>
                        `;
                        peripheralsList.appendChild(listItem);

                        // Add click event for preview button
                        listItem.querySelector("button").addEventListener("click", () => {
                            showPeripheralPreview(peripheral);
                        });
                    });
                } else {
                    peripheralsList.innerHTML = "<li class='list-group-item'>No peripherals found.</li>";
                }
            })
            .catch(error => console.error("Error fetching peripherals:", error));
    }

    // Show peripheral preview
    function showPeripheralPreview(peripheral) {
        previewName.textContent = peripheral.name;
        previewProperties.textContent = JSON.stringify(peripheral.properties, null, 2);
        peripheralPreview.classList.remove("d-none");

        // Add event listener for test connection
        document.getElementById("test-connection").onclick = () => {
            testPeripheralConnection(peripheral.id);
        };

        // Add event listener for test device
        document.getElementById("test-device").onclick = () => {
            redirectToDashboard(peripheral.id);
        };
    }

    // Test connection
    function testPeripheralConnection(peripheralId) {
        fetch(`/peripherals/test-connection/${peripheralId}`)
            .then(response => response.json())
            .then(data => alert(data.message || "Connection test successful."))
            .catch(error => alert("Failed to test connection."));
    }

    // Redirect to dashboard
    function redirectToDashboard(peripheralId) {
        window.location.href = `/dashboard?peripheral_id=${peripheralId}`;
    }

    // Add peripheral form submission
    addPeripheralForm.addEventListener("submit", (event) => {
        event.preventDefault();

        const name = document.getElementById("peripheral-name").value;
        const properties = document.getElementById("peripheral-properties").value;

        fetch("/peripherals/add", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
            },
            body: JSON.stringify({ name, properties: JSON.parse(properties) }),
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message || "Peripheral added successfully.");
                fetchPeripherals();
                addPeripheralForm.reset();
            })
            .catch(error => {
                alert("Failed to add peripheral.");
                console.error(error);
            });
    });

    // Initial fetch
    fetchPeripherals();
});

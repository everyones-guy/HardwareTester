document.addEventListener("DOMContentLoaded", () => {
    const peripheralsList = document.getElementById("peripherals-list");
    const peripheralPreview = document.getElementById("peripheral-preview");
    const previewName = document.getElementById("preview-name");
    const previewProperties = document.getElementById("preview-properties");
    const addPeripheralForm = document.getElementById("add-peripheral-form");

    /**
     * Fetch and display peripherals
     */
    async function fetchPeripherals() {
        try {
            const data = await apiCall("/peripherals/list", "GET");

            peripheralsList.innerHTML = "";
            if (data.success && data.peripherals.length > 0) {
                data.peripherals.forEach((peripheral) => {
                    peripheralsList.innerHTML += `
                        <li class="list-group-item d-flex justify-content-between">
                            <span>${peripheral.name}</span>
                            <button class="btn btn-info btn-sm preview-peripheral" data-id="${peripheral.id}" data-properties='${JSON.stringify(peripheral.properties)}'>Preview</button>
                        </li>`;
                });

                attachPreviewListeners();
            } else {
                peripheralsList.innerHTML = "<li class='list-group-item text-danger'>No peripherals found.</li>";
            }
        } catch (error) {
            console.error("Error fetching peripherals:", error);
            peripheralsList.innerHTML = "<li class='list-group-item text-danger'>Failed to load peripherals.</li>";
        }
    }

    /**
     * Show peripheral preview
     */
    function attachPreviewListeners() {
        document.querySelectorAll(".preview-peripheral").forEach((button) => {
            button.addEventListener("click", () => {
                const peripheralId = button.getAttribute("data-id");
                const properties = JSON.parse(button.getAttribute("data-properties"));

                previewName.textContent = peripheralId;
                previewProperties.textContent = JSON.stringify(properties, null, 2);
                peripheralPreview.classList.remove("d-none");

                document.getElementById("test-connection").onclick = () => testPeripheralConnection(peripheralId);
                document.getElementById("test-device").onclick = () => redirectToDashboard(peripheralId);
            });
        });
    }

    /**
     * Test connection
     */
    async function testPeripheralConnection(peripheralId) {
        try {
            const data = await apiCall(`/peripherals/test-connection/${peripheralId}`, "GET");
            alert(data.message || "Connection test successful.");
        } catch (error) {
            console.error("Connection test error:", error);
            alert("Failed to test connection.");
        }
    }

    /**
     * Redirect to dashboard
     */
    function redirectToDashboard(peripheralId) {
        window.location.href = `/dashboard?peripheral_id=${peripheralId}`;
    }

    /**
     * Handle adding a new peripheral
     */
    if (addPeripheralForm) {
        addPeripheralForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const name = document.getElementById("peripheral-name").value;
            const propertiesInput = document.getElementById("peripheral-properties").value;

            try {
                const properties = JSON.parse(propertiesInput); // Ensure valid JSON

                const response = await apiCall("/peripherals/add", "POST", { name, properties });
                alert(response.message || "Peripheral added successfully.");
                fetchPeripherals();
                addPeripheralForm.reset();
            } catch (error) {
                console.error("Error adding peripheral:", error);
                alert("Failed to add peripheral. Check console for details.");
            }
        });
    }

    // **Initial fetch**
    fetchPeripherals();
});

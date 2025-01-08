document.addEventListener("DOMContentLoaded", () => {
    const discoverDeviceForm = document.getElementById("discover-device-form");
    const deviceDetailsCard = document.getElementById("device-details");
    const deviceInfoContainer = document.getElementById("device-info");
    const deviceSettingsContainer = document.getElementById("device-settings");

    discoverDeviceForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const deviceId = document.getElementById("device-id").value;

        if (!deviceId) {
            alert("Please enter a Device ID.");
            return;
        }

        const discoverButton = discoverDeviceForm.querySelector("button[type='submit']");
        discoverButton.disabled = true;
        discoverButton.textContent = "Discovering...";

        fetch("/hardware/discover-device", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').getAttribute("content"),
            },
            body: JSON.stringify({ device_id: deviceId }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to discover device.");
                }
                return response.json();
            })
            .then((data) => {
                const { device } = data;
                const deviceInfo = `
                    <p><strong>Name:</strong> ${device.name}</p>
                    <p><strong>Firmware:</strong> ${device.device_metadata.firmware}</p>
                    <p><strong>Model:</strong> ${device.device_metadata.model}</p>
                `;
                const deviceSettings = device.settings.menu
                    .map(
                        (menu) => `
                        <div class="mt-3">
                            <h5>${menu.name}</h5>
                            <ul class="list-group">
                                ${menu.options.map((opt) => `<li class="list-group-item">${opt}</li>`).join("")}
                            </ul>
                        </div>
                    `
                    )
                    .join("");

                deviceInfoContainer.innerHTML = deviceInfo;
                deviceSettingsContainer.innerHTML = deviceSettings;
                deviceDetailsCard.classList.remove("d-none");
            })
            .catch((error) => {
                alert(`Error: ${error.message}`);
            })
            .finally(() => {
                discoverButton.disabled = false;
                discoverButton.textContent = "Discover";
            });
    });
});

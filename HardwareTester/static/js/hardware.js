$(document).ready(function () {
    const discoverDeviceForm = $("#discover-device-form");
    const deviceDetailsCard = $("#device-details");
    const deviceInfoContainer = $("#device-info");
    const deviceSettingsContainer = $("#device-settings");

    discoverDeviceForm.on("submit", function (event) {
        event.preventDefault();
        const deviceId = $("#device-id").val();

        if (!deviceId) {
            alert("Please enter a Device ID.");
            return;
        }

        const discoverButton = discoverDeviceForm.find("button[type='submit']");
        discoverButton.prop("disabled", true).text("Discovering...");

        $.ajax({
            url: "/hardware/discover-device",
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": $("meta[name='csrf-token']").attr("content"),
            },
            data: JSON.stringify({ device_id: deviceId }),
            success: function (data) {
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

                deviceInfoContainer.html(deviceInfo);
                deviceSettingsContainer.html(deviceSettings);
                deviceDetailsCard.removeClass("d-none");
            },
            error: function (xhr) {
                alert(`Error: ${xhr.responseJSON?.message || xhr.statusText}`);
            },
            complete: function () {
                discoverButton.prop("disabled", false).text("Discover");
            },
        });
    });

    $("#firmware-form").on("submit", function (event) {
        event.preventDefault();

        const formData = new FormData();
        formData.append("firmware", $("#firmware")[0].files[0]);
        const machines = $("#machines").val();
        machines.forEach(machine => formData.append("machines", machine));

        $.ajax({
            url: "/firmware/upload",
            method: "POST",
            processData: false,
            contentType: false,
            data: formData,
            success: function (result) {
                if (result.success) {
                    alert("Firmware uploaded successfully!");
                } else {
                    alert(`Error: ${result.error}`);
                }
            },
            error: function (xhr) {
                alert(`Error: ${xhr.responseJSON?.message || xhr.statusText}`);
            },
        });
    });
});
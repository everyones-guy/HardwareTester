$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Handle tab switching
    function handleTabs() {
        $(".list-group-item").on("click", function (e) {
            e.preventDefault();
            const targetId = $(this).attr("href").substring(1);

            // Update active tab class
            $(".list-group-item").removeClass("active");
            $(this).addClass("active");

            // Update tab-pane visibility
            $(".tab-pane").removeClass("show active");
            $(`#${targetId}`).addClass("show active");

            // Initialize or load data based on tab
            if (targetId === "add-emulator-tab" && typeof initializeEmulatorForm === "function") {
                initializeEmulatorForm();
            } else if (targetId === "compare-emulators-tab" && typeof loadAvailableEmulators === "function") {
                loadAvailableEmulators();
            }
        });
    }

    // Add components visually to the dashboard
    function addComponent(id, type, x = 50, y = 50) {
        const element = $(`
            <div id="component-${id}" class="draggable" 
                data-id="${id}" data-type="${type}" 
                style="position: absolute; left: ${x}px; top: ${y}px;">
                <div class="component-body p-2 text-white bg-primary rounded">${type}</div>
            </div>
        `);
        canvas.append(element);
        enableDrag(element);
    }

    // Handle real-time updates using Socket.IO
    socket.on("device_update", (data) => {
        const { id, type, state, value } = data;
        const component = $(`#component-${id}`);
        if (component.length) {
            animateDevice(component, type, state, value);
        }
    });

    // Animate devices based on type and state
    function animateDevice(element, type, state, value) {
        const animations = {
            valve: animateValve,
            motor: animateMotor,
            sensor: animateSensor,
        };

        if (animations[type]) {
            animations[type](element, state, value);
        }
    }

    // Valve animations
    function animateValve(element, state, value) {
        if (state === "open") {
            anime({
                targets: element[0],
                scale: 1.2,
                duration: 800,
                direction: "alternate",
                easing: "easeInOutQuad",
            });
            element.find(".component-body").text(`Valve Open (${value}%)`);
        } else if (state === "closed") {
            anime({
                targets: element[0],
                scale: 1.0,
                duration: 800,
                easing: "easeInOutQuad",
            });
            element.find(".component-body").text("Valve Closed");
        } else if (state === "flow") {
            anime({
                targets: element[0],
                rotate: 360,
                duration: 1000,
                easing: "linear",
                loop: true,
            });
            element.find(".component-body").text(`Flow: ${value} L/s`);
        }
    }

    // Motor animations
    function animateMotor(element, state, speed) {
        if (state === "running") {
            anime({
                targets: element[0],
                rotate: 360,
                duration: 1000 / speed,
                easing: "linear",
                loop: true,
            });
            element.find(".component-body").text(`Motor Running (${speed} RPM)`);
        } else if (state === "stopped") {
            anime.remove(element[0]); // Stop ongoing animation
            element.find(".component-body").text("Motor Stopped");
        }
    }

    // Sensor animations
    function animateSensor(element, state, value) {
        element.find(".component-body").text(`Sensor (${state}): ${value}`);
    }

    // Enable drag-and-drop functionality for elements
    function enableDrag(element) {
        interact(element[0]).draggable({
            listeners: {
                move(event) {
                    const target = event.target;
                    const x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;

                    if (x >= 0 && y >= 0 && x <= canvas.width() - 100 && y <= canvas.height() - 50) {
                        target.style.transform = `translate(${x}px, ${y}px)`;
                        target.setAttribute("data-x", x);
                        target.setAttribute("data-y", y);
                    }
                },
            },
        });
    }

    // Fetch overview data for the dashboard
    function loadOverview() {
        apiCall(
            "/dashboard/overview",
            "GET",
            null,
            (data) => {
                const list = $("#dashboard-data ul");
                list.empty();

                if (data && Array.isArray(data)) {
                    data.forEach((item) => {
                        list.append(`<li>${item.title}: ${item.description}</li>`);
                    });
                } else {
                    list.append("<li>No data available.</li>");
                }
            },
            () => console.error("Failed to load overview data.")
        );
    }

    // Discover devices
    $("#discover-devices").click(function () {
        apiRequest("/serial/discover", "GET")
            .done((data) => {
                const deviceList = $("#device-list");
                deviceList.empty();
                if (data.success && data.devices.length) {
                    data.devices.forEach(device => {
                        deviceList.append(`<li>${device.port} - ${JSON.stringify(device.info)}</li>`);
                    });
                } else {
                    deviceList.append("<li>No devices discovered.</li>");
                }
            })
            .fail(() => alert("Failed to discover devices."));
    });

    // Configure a device
    $("#configure-device").submit(function (event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        const payload = {};
        formDatal.data.forEach(field => payload[field.name] = field.value);

        apiRequest("/serial/configure", "POST", payload)
            .done((data) => {
                alert(data.success ? data.message : `Error: ${data.error}`);
            })
            .fail(() => alert("Failed to configure device."));
    });

    // Save and load configurations
    $("#save-config").click(function () {
        const layout = [];
        $(".draggable").each(function () {
            const id = $(this).data("id");
            const type = $(this).data("type");
            const x = $(this).position().left;
            const y = $(this).position().top;
            layout.push({ id, type, x, y });
        });

        apiRequest("/save-configuration", "POST", { layout })
            .done((response) => alert(response.message))
            .fail(() => alert("Failed to save configuration."));
    });

    $("#load-config").click(function () {
        apiRequest("/load-configuration", "GET")
            .done((data) => {
                if (data.success) {
                    canvas.empty();
                    data.layout.forEach(item => addComponent(item.id, item.type, item.x, item.y));
                } else {
                    alert(data.error || "Failed to load configuration.");
                }
            })
            .fail(() => alert("Failed to load configuration."));
    });


    // Event handler for stopping emulators
    $(document).on("click", ".stop-emulator", function () {
        const emulatorId = $(this).data("id");
        apiRequest(`/emulators/stop`, "POST", { id: emulatorId })
            .done(() => {
                alert(`Emulator ${emulatorId} stopped successfully.`);
                loadEmulators(); // Refresh the list after stopping
            })
            .fail(() => alert("Failed to stop emulator."));
    });


    function loadLogs() {
        const container = $("#log-output");
        container.html("<p>Loading logs...</p>"); // Placeholder while fetching logs

        apiRequest("/logs/recent", "GET")
            .done((data) => {
                container.empty(); // Clear placeholder
                if (data.success && Array.isArray(data.logs) && data.logs.length > 0) {
                    data.logs.forEach((log) => {
                        container.append($("<p>").text(log.trim())); // Escape HTML characters and trim
                    });
                } else {
                    container.append("<p>No logs available.</p>");
                }
            })
            .fail((xhr, status, error) => {
                container.empty();
                console.error("Error loading logs:", error);
                container.append(`<p class="text-danger">Failed to load logs: ${xhr.statusText}</p>`);
            });
    }


    function loadSettings() {
        apiRequest("/settings/global/list", "GET")
            .done((data) => {
                const list = $("#global-settings-list");
                list.empty();
                if (data.success && Array.isArray(data.settings)) {
                    data.settings.forEach((setting) => {
                        list.append(`
                        <li class="list-group-item">
                            <strong>${setting.key}</strong>: ${JSON.stringify(setting.value)}
                        </li>
                    `);
                    });
                } else {
                    list.append("<li class='list-group-item'>No settings available.</li>");
                }
            })
            .fail(() => alert("Failed to load settings."));
    }

    // Initialize tabs and data loading
    handleTabs();
    loadOverview();
    loadLogs();
    loadSettings();
});

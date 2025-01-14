$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Function to handle tab switching
    function handleTabs() {
        $(".list-group-item").click(function () {
            const targetId = $(this).attr("href").substring(1);

            // Update tab-pane visibility
            $(".tab-pane").removeClass("show active");
            $(`#${targetId}`).addClass("show active");

            // Specific behaviors for the Serial tab
            if (targetId === "serial") {
                $("#device-discovery").show();
                $("#device-config-form").show();
            } else {
                $("#device-discovery").hide();
                $("#device-config-form").hide();
            }
        });
    }

    // Function to add a device visually
    function addComponent(id, type, x = 50, y = 50) {
        const element = $(`<div id="component-${id}" class="draggable"
                    data-id="${id}" data-type="${type}"
                    style="position: absolute; left: ${x}px; top: ${y}px;">
                    <div class="component-body p-2 text-white bg-primary rounded">${type}</div>
                </div>`);
        canvas.append(element);
        enableDrag(element);
    }

    // Real-time updates using Socket.IO
    socket.on("device_update", (data) => {
        const { id, type, state, value } = data;
        const component = $(`#component-${id}`);
        if (component.length) {
            animateDevice(component, type, state, value);
        }
    });

    // Function to animate devices
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

    // Specific animations for valves
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

    // Specific animations for motors
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
            anime.remove(element[0]); // Stop any ongoing animation
            element.find(".component-body").text("Motor Stopped");
        }
    }

    // Specific animations for sensors
    function animateSensor(element, state, value) {
        element.find(".component-body").text(`Sensor (${state}): ${value}`);
    }

    // Drag-and-drop functionality
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

    // API request helper
    function apiRequest(url, method, data = null) {
        return $.ajax({
            url: url,
            type: method,
            data: data ? JSON.stringify(data) : null,
            contentType: "application/json",
        });
    }

    // Discover devices
    $("#discover-devices").click(function () {
        apiRequest("/serial/discover", "GET")
            .done((data) => {
                if (data.success) {
                    const deviceList = $("#device-list");
                    deviceList.empty();
                    data.devices.forEach(device => {
                        deviceList.append(`<li>${device.port} - ${JSON.stringify(device.info)}</li>`);
                    });
                } else {
                    alert("No devices discovered.");
                }
            })
            .fail(() => alert("Failed to discover devices."));
    });

    // Configure a device
    $("#configure-device").submit(function (event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        const payload = {};
        formData.forEach(field => payload[field.name] = field.value);

        apiRequest("/serial/configure", "POST", payload)
            .done((data) => {
                if (data.success) {
                    alert(data.message);
                } else {
                    alert(`Error: ${data.error}`);
                }
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

    // Dashboard functionality
    function loadOverview() {
        console.log("Overview section loaded.");
    }

    function loadEmulators() {
        apiRequest("/emulators/list", "GET")
            .done((data) => {
                const list = $("#emulator-list");
                list.empty();
                if (data.success) {
                    data.emulators.forEach((emulator) => {
                        list.append(`
                        <li class="list-group-item">
                            <strong>${emulator.name}</strong> - Status: ${emulator.status}
                            <button class="btn btn-danger btn-sm float-end stop-emulator" data-id="${emulator.id}">Stop</button>
                        </li>
                    `);
                    });
                } else {
                    list.append(`<li class="list-group-item text-danger">Error loading emulators.</li>`);
                }
            });
    }

    function loadLogs() {
        apiRequest("/logs/recent", "GET")
            .done((data) => {
                const container = $("#log-output");
                container.empty();
                if (data.success) {
                    data.logs.forEach((log) => {
                        container.append(`<p>${log}</p>`);
                    });
                } else {
                    container.append("<p>Error loading logs.</p>");
                }
            });
    }

    function loadSettings() {
        apiRequest("/settings/global", "GET")
            .done((data) => {
                const list = $("#global-settings-list");
                list.empty();
                if (data.success) {
                    data.settings.forEach((setting) => {
                        list.append(`
                        <li class="list-group-item">
                            <strong>${setting.key}</strong>: ${JSON.stringify(setting.value)}
                        </li>
                    `);
                    });
                } else {
                    list.append("<li class='list-group-item text-danger'>Error loading settings.</li>");
                }
            });
    }

    // Initialize dashboard
    handleTabs();
    loadOverview();
    loadEmulators();
    loadLogs();
    loadSettings();
});

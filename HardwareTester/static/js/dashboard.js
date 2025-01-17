$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Utility function for API calls
    function apiRequest(endpoint, method, data, onSuccess, onError) {
        $.ajax({
            url: endpoint,
            type: method,
            contentType: method === "POST" ? "application/json" : undefined,
            data: method === "POST" ? JSON.stringify(data) : null,
            success: onSuccess,
            error: onError || function (xhr) {
                console.error(`API Error [${method} ${endpoint}]:`, xhr.responseText);
                alert(`An error occurred: ${xhr.statusText} (${xhr.status}).`);
            },
        });
    }

    // Tab switching functionality
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

            // Load specific data when switching tabs
            if (targetId === "emulators" && typeof loadAvailableEmulators === "function") {
                loadAvailableEmulators();
            } else if (targetId === "logs" && typeof loadLogs === "function") {
                loadLogs();
            } else if (targetId === "settings" && typeof loadSettings === "function") {
                loadSettings();
            }
        });
    }

    // Add components visually
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

    // Real-time device updates
    socket.on("device_update", (data) => {
        const { id, type, state, value } = data;
        const component = $(`#component-${id}`);
        if (component.length) {
            animateDevice(component, type, state, value);
        }
    });

    // Animate devices
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

    function animateValve(element, state, value) {
        if (state === "open") {
            anime({ targets: element[0], scale: 1.2, duration: 800, easing: "easeInOutQuad" });
            element.find(".component-body").text(`Valve Open (${value}%)`);
        } else if (state === "closed") {
            anime({ targets: element[0], scale: 1.0, duration: 800, easing: "easeInOutQuad" });
            element.find(".component-body").text("Valve Closed");
        }
    }

    function animateMotor(element, state, speed) {
        if (state === "running") {
            anime({ targets: element[0], rotate: 360, duration: 1000 / speed, easing: "linear", loop: true });
            element.find(".component-body").text(`Motor Running (${speed} RPM)`);
        }
    }

    function animateSensor(element, state, value) {
        element.find(".component-body").text(`Sensor (${state}): ${value}`);
    }

    // Load and display logs
    function loadLogs() {
        apiRequest("/logs/recent", "GET", null, (data) => {
            const container = $("#log-output");
            container.empty();
            if (data.success && data.logs.length > 0) {
                data.logs.forEach((log) => container.append(`<p>${log}</p>`));
            } else {
                container.append("<p>No logs available.</p>");
            }
        });
    }

    // Discover devices
    $("#discover-devices").click(function () {
        apiRequest("/serial/discover", "GET", null, (data) => {
            const deviceList = $("#device-list");
            deviceList.empty();
            if (data.success && data.devices.length) {
                data.devices.forEach((device) => deviceList.append(`<li>${device.port} - ${JSON.stringify(device.info)}</li>`));
            } else {
                deviceList.append("<li>No devices discovered.</li>");
            }
        });
    });

    // Configure devices
    $("#configure-device").submit(function (event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        const payload = {};
        formData.forEach((field) => (payload[field.name] = field.value));

        apiRequest("/serial/configure", "POST", payload, (data) => {
            alert(data.success ? data.message : `Error: ${data.error}`);
        });
    });

    // Save and load dashboard configuration
    $("#save-config").click(function () {
        const layout = [];
        $(".draggable").each(function () {
            const id = $(this).data("id");
            const type = $(this).data("type");
            const x = $(this).position().left;
            const y = $(this).position().top;
            layout.push({ id, type, x, y });
        });

        apiRequest("/save-configuration", "POST", { layout }, (response) => alert(response.message));
    });

    $("#load-config").click(function () {
        apiRequest("/load-configuration", "GET", null, (data) => {
            if (data.success) {
                canvas.empty();
                data.layout.forEach((item) => addComponent(item.id, item.type, item.x, item.y));
            } else {
                alert(data.error || "Failed to load configuration.");
            }
        });
    });

    // Initialize dashboard
    handleTabs();
    loadLogs();
    loadOverview();
});

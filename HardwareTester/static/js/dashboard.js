$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Function to add a valve or peripheral visually
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
    socket.on("valve_update", (data) => {
        const { id, state, value } = data;
        const component = $(`#component-${id}`);
        if (component.length) {
            animateValve(component, state, value);
        }
    });

    // Function to animate valves
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

    // Example reusable API request helper
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
                    deviceList.append(`<li>${data.device_info.port} - ${JSON.stringify(data.device_info)}</li>`);
                } else {
                    alert("No devices discovered.");
                }
            })
            .fail(() => alert("Failed to discover devices."));
    });

    // Initialize dashboard functionality
    loadOverview();
    loadEmulators();
    loadLogs();
    loadSettings();
});

$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Function to handle tab switching
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

            // Initialize emulator form when the emulator tab is selected
            if (targetId === "add-emulator-tab") {
                if (typeof initializeEmulatorForm === "function") {
                    initializeEmulatorForm();
                }
            }
        });
    }

    // Function to add a device visually
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
    function apiRequest(url, method, data = {}) {
        return $.ajax({
            url: url,
            method: method,
            data: method === "GET" ? undefined : JSON.stringify(data),
            contentType: "application/json",
        });
    }

    // Dashboard functionality
    function loadOverview() {
        $.ajax({
            url: "/dashboard/overview",
            method: "GET",
            success: function (data) {
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
            error: function () {
                console.error("Failed to load overview data.");
            },
        });
    }

    // Initialize dashboard
    handleTabs();
    loadOverview();
});

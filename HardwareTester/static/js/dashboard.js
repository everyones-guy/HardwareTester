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

    // Initialize tabs and data loading
    handleTabs();
    loadOverview();
});

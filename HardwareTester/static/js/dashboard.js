$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Function to handle tab switching
    function handleTabs() {
        $(".list-group-item").on("click", function (e) {
            e.preventDefault();
            const targetId = $(this).attr("href").substring(1);

            $(".list-group-item").removeClass("active");
            $(this).addClass("active");

            $(".tab-pane").removeClass("show active");
            $(`#${targetId}`).addClass("show active");

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

    // Function to load overview data
    async function loadOverview() {
        try {
            const data = await apiCall("/api/dashboard/overview", "GET");
            const list = $("#dashboard-data ul");
            list.empty();

            if (data && Array.isArray(data.data)) {
                data.data.forEach((item) => {
                    list.append(`<li>${item.title}: ${item.description}</li>`);
                });
            } else {
                list.append("<li>No data available.</li>");
            }
        } catch (error) {
            console.error("Failed to load overview data:", error);
        }
    }

    // Function to load system health metrics
    async function loadSystemHealth() {
        try {
            const data = await apiCall("/api/dashboard/system-health", "GET");
            if (data.success) {
                $("#cpu-usage").text(`CPU Usage: ${data.data.cpu_usage}%`);
                $("#memory-usage").text(`Memory Usage: ${data.data.memory_usage}%`);
                $("#disk-usage").text(`Disk Usage: ${data.data.disk_usage}%`);
            } else {
                console.error("Failed to fetch system health:", data.error);
            }
        } catch (error) {
            console.error("Error fetching system health:", error);
        }
    }

    // Function to load test execution metrics
    async function loadTestMetrics() {
        try {
            const data = await apiCall("/api/dashboard/test-metrics", "GET");
            if (data.success) {
                $("#total-tests").text(`Total Tests: ${data.data.total_test_plans}`);
                $("#passed-tests").text(`Passed: ${data.data.passed_tests}`);
                $("#failed-tests").text(`Failed: ${data.data.failed_tests}`);
                $("#pass-rate").text(`Pass Rate: ${data.data.pass_rate}`);
            } else {
                console.error("Failed to fetch test metrics:", data.error);
            }
        } catch (error) {
            console.error("Error fetching test metrics:", error);
        }
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

    // Initialize dashboard
    handleTabs();
    loadOverview();
    loadSystemHealth();
    loadTestMetrics();
});

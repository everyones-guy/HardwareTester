
document.addEventListener("DOMContentLoaded", () => {
    // Initialize Charts
    initializeActivityChart();
    initializePerformanceChart();
    loadAnalyticsTable();

    // Fetch data for charts
    function fetchAnalyticsData(endpoint, callback) {
        fetch(endpoint)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Failed to fetch data");
                }
                return response.json();
            })
            .then(data => callback(data))
            .catch(error => console.error("Error fetching analytics data:", error));
    }

    // Initialize Activity Chart
    function initializeActivityChart() {
        const ctx = document.getElementById("activityChart").getContext("2d");
        fetchAnalyticsData("/analytics/activity", (data) => {
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Activity",
                        data: data.values,
                        borderColor: "rgba(75, 192, 192, 1)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: "top",
                        }
                    }
                }
            });
        });
    }

    // Initialize Performance Chart
    function initializePerformanceChart() {
        const ctx = document.getElementById("performanceChart").getContext("2d");
        fetchAnalyticsData("/analytics/performance", (data) => {
            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Performance",
                        data: data.values,
                        backgroundColor: "rgba(54, 162, 235, 0.5)",
                        borderColor: "rgba(54, 162, 235, 1)",
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: "top",
                        }
                    }
                }
            });
        });
    }

    // Load Analytics Table
    function loadAnalyticsTable() {
        fetchAnalyticsData("/analytics/insights", (data) => {
            const tableBody = document.querySelector("#analyticsTable tbody");
            tableBody.innerHTML = ""; // Clear table before adding data

            data.forEach(item => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${item.metric}</td>
                    <td>${item.value}</td>
                    <td class="${item.change > 0 ? 'text-success' : 'text-danger'}">
                        ${item.change > 0 ? '+' : ''}${item.change}%
                    </td>
                `;
                tableBody.appendChild(row);
            });
        });
    }
});


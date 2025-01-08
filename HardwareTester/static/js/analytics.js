document.addEventListener("DOMContentLoaded", () => {
    // Initialize Charts
    initializeActivityChart();
    initializePerformanceChart();
    loadAnalyticsTable();

    function fetchAnalyticsData(endpoint, onSuccess, onError) {
        fetch(endpoint)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Failed to fetch data");
                }
                return response.json();
            })
            .then(data => onSuccess(data))
            .catch(error => {
                console.error("Error fetching analytics data:", error);
                if (onError) onError(error);
            });
    }

    function initializeActivityChart() {
        const ctx = document.getElementById("activityChart").getContext("2d");
        const container = document.getElementById("activityChartContainer");

        fetchAnalyticsData(
            "/analytics/activity",
            (data) => {
                container.style.display = "none";
                document.getElementById("activityChart").style.display = "block";
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
                            legend: { display: true, position: "top" },
                        }
                    }
                });
            },
            () => {
                container.innerHTML = "<p class='text-danger'>Failed to load Activity Chart.</p>";
            }
        );
    }

    function initializePerformanceChart() {
        const ctx = document.getElementById("performanceChart").getContext("2d");
        const container = document.getElementById("performanceChartContainer");

        fetchAnalyticsData(
            "/analytics/performance",
            (data) => {
                container.style.display = "none";
                document.getElementById("performanceChart").style.display = "block";
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
                            legend: { display: true, position: "top" },
                        }
                    }
                });
            },
            () => {
                container.innerHTML = "<p class='text-danger'>Failed to load Performance Chart.</p>";
            }
        );
    }

    function loadAnalyticsTable() {
        const container = document.getElementById("analyticsTableContainer");
        const table = document.getElementById("analyticsTable");

        fetchAnalyticsData(
            "/analytics/insights",
            (data) => {
                container.style.display = "none";
                table.style.display = "table";
                const tableBody = table.querySelector("tbody");
                tableBody.innerHTML = "";

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
            },
            () => {
                container.innerHTML = "<p class='text-danger'>Failed to load Data Insights.</p>";
            }
        );
    }
});

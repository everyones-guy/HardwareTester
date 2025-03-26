$(document).ready(function () {
    // Initialize Charts
    initializeActivityChart();
    initializePerformanceChart();
    loadAnalyticsTable();

    // Fetch analytics data using apiCall
    async function fetchAnalyticsData(endpoint) {
        try {
            return await apiCall(endpoint, "GET");
        } catch (error) {
            console.error(`Failed to fetch analytics data from ${endpoint}:`, error);
            return null;
        }
    }

    async function initializeActivityChart() {
        const ctx = $("#activityChart")[0].getContext("2d");
        const container = $("#activityChartContainer");

        const data = await fetchAnalyticsData("/analytics/activity");
        if (!data) {
            container.html("<p class='text-danger'>Failed to load Activity Chart.</p>");
            return;
        }

        container.hide();
        $("#activityChart").show();

        new Chart(ctx, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Activity",
                        data: data.values,
                        borderColor: "rgba(75, 192, 192, 1)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true, position: "top" },
                },
            },
        });
    }

    async function initializePerformanceChart() {
        const ctx = $("#performanceChart")[0].getContext("2d");
        const container = $("#performanceChartContainer");

        const data = await fetchAnalyticsData("/analytics/performance");
        if (!data) {
            container.html("<p class='text-danger'>Failed to load Performance Chart.</p>");
            return;
        }

        container.hide();
        $("#performanceChart").show();

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Performance",
                        data: data.values,
                        backgroundColor: "rgba(54, 162, 235, 0.5)",
                        borderColor: "rgba(54, 162, 235, 1)",
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true, position: "top" },
                },
            },
        });
    }

    async function loadAnalyticsTable() {
        const container = $("#analyticsTableContainer");
        const table = $("#analyticsTable");

        const data = await fetchAnalyticsData("/analytics/insights");
        if (!data) {
            container.html("<p class='text-danger'>Failed to load Data Insights.</p>");
            return;
        }

        container.hide();
        table.show();
        const tableBody = table.find("tbody");
        tableBody.empty();

        data.forEach((item) => {
            const row = `
                <tr>
                    <td>${item.metric}</td>
                    <td>${item.value}</td>
                    <td class="${item.change > 0 ? "text-success" : "text-danger"}">
                        ${item.change > 0 ? "+" : ""}${item.change}%
                    </td>
                </tr>
            `;
            tableBody.append(row);
        });
    }
});

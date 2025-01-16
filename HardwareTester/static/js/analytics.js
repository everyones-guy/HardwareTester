$(document).ready(function () {
    // Initialize Charts
    initializeActivityChart();
    initializePerformanceChart();
    loadAnalyticsTable();

    function fetchAnalyticsData(endpoint, onSuccess, onError) {
        $.ajax({
            url: endpoint,
            method: "GET",
            dataType: "json",
            success: function (data) {
                onSuccess(data);
            },
            error: function (xhr, status, error) {
                console.error("Error fetching analytics data:", error);
                if (onError) onError(error);
            },
        });
    }

    function initializeActivityChart() {
        const ctx = $("#activityChart")[0].getContext("2d");
        const container = $("#activityChartContainer");

        fetchAnalyticsData(
            "/analytics/activity",
            (data) => {
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
            },
            () => {
                container.html("<p class='text-danger'>Failed to load Activity Chart.</p>");
            }
        );
    }

    function initializePerformanceChart() {
        const ctx = $("#performanceChart")[0].getContext("2d");
        const container = $("#performanceChartContainer");

        fetchAnalyticsData(
            "/analytics/performance",
            (data) => {
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
            },
            () => {
                container.html("<p class='text-danger'>Failed to load Performance Chart.</p>");
            }
        );
    }

    function loadAnalyticsTable() {
        const container = $("#analyticsTableContainer");
        const table = $("#analyticsTable");

        fetchAnalyticsData(
            "/analytics/insights",
            (data) => {
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
            },
            () => {
                container.html("<p class='text-danger'>Failed to load Data Insights.</p>");
            }
        );
    }
});

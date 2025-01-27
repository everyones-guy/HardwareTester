// setup.js for the browser
globalThis.$ = globalThis.jQuery = jQuery;

// Utility function for API calls
globalThis.apiCall = function (endpoint, method, data = {}, onSuccess, onError) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content; // Dynamically fetch token
    const isPostMethod = method.toUpperCase() === "POST";
    const isGetMethod = method.toUpperCase() === "GET";

    $.ajax({
        url: endpoint,
        type: method,
        contentType: isGetMethod ? undefined : "application/json",
        headers: {
            "X-CSRFToken": csrfToken, // Attach CSRF token dynamically
        },
        data: isGetMethod ? undefined : JSON.stringify(data),
        processData: false,
        success: function (response) {
            if (onSuccess) {
                onSuccess(response);
            }
        },
        error: function (xhr) {
            const errorMessage = xhr.responseJSON?.error || xhr.statusText || "An error occurred while communicating with the server.";
            console.error(`API Error (${method} ${endpoint}):`, errorMessage);
            if (onError) {
                onError(xhr);
            } else {
                alert(errorMessage);
            }
        },
    });
};

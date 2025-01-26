// setup.js for the browser
globalThis.$ = globalThis.jQuery = jQuery;

// Utility function for API calls
globalThis.apiCall = function (endpoint, method, data = {}, onSuccess, onError) {
    const isPostMethod = method.toUpperCase() === "POST";
    const isGetMethod = method.toUpperCase() === "GET";

    $.ajax({
        url: endpoint,
        type: method,
        contentType: isGetMethod ? undefined : "application/json", // Content-Type for non-GET methods
        headers: {
            "X-CSRFToken": $("[name=csrf_token]").val(), // Include CSRF token
        },
        data: isGetMethod ? undefined : JSON.stringify(data), // Only stringify for POST/PUT
        processData: false, // Ensure no data processing by jQuery
        success: function (response) {
            if (onSuccess) {
                onSuccess(response); // Call the success callback
            }
        },
        error: function (xhr) {
            const errorMessage = xhr.responseJSON?.error || xhr.statusText || "An error occurred while communicating with the server.";
            console.error(`API Error (${method} ${endpoint}):`, errorMessage);
            if (onError) {
                onError(xhr); // Call the error callback if provided
            } else {
                alert(errorMessage); // Fallback to alert for unhandled errors
            }
        },
    });
};


$(document).ready(function () {
    $("#upload-spec-sheet-form").on("submit", function (e) {
        e.preventDefault(); // Prevent form from submitting traditionally
        const formData = new FormData(this); // Prepare the form data
        $.ajax({
            url: "/upload/spec-sheets/upload", // Endpoint for uploading spec sheets
            type: "POST",
            headers: {
                "X-CSRFToken": $('meta[name="csrf-token"]').attr('content')  // Ensure CSRF token is sent
            },
            data: formData,
            processData: false, // Prevent processing of data into a query string
            contentType: false, // Don't set content-type header
            success: function (response) {
                // Show success alert
                const message = response.message || "Spec sheet uploaded successfully.";
                alert(message);
            },
            error: function (xhr) {
                // Show error alert
                const errorMessage = xhr.responseJSON?.error || "Failed to upload spec sheet.";
                alert(errorMessage);
            },
        });
    });
});


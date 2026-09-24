document.addEventListener("DOMContentLoaded", function () {

    // =====================================================
    // GET ELEMENTS
    // =====================================================

    const fileInput = document.getElementById("fileinput");
    const scanButton = document.getElementById("ScanButton");
    const selectedFile = document.getElementById("selectedFile");


    // =====================================================
    // SELECT IMAGE BUTTON
    // =====================================================

    if (scanButton && fileInput) {

        scanButton.addEventListener("click", function () {

            fileInput.click();

        });

    }


    // =====================================================
    // IMAGE SELECTED
    // =====================================================

    if (fileInput) {

        fileInput.addEventListener("change", function () {

            if (fileInput.files.length === 0) {

                if (selectedFile) {

                    selectedFile.textContent =
                        "No image selected";

                }

                return;

            }


            const file = fileInput.files[0];


            // -------------------------------------------------
            // CHECK FILE TYPE
            // -------------------------------------------------

            if (!file.type.startsWith("image/")) {

                alert("Please select an image file.");

                fileInput.value = "";

                if (selectedFile) {

                    selectedFile.textContent =
                        "No image selected";

                }

                return;

            }


            // -------------------------------------------------
            // CHECK FILE SIZE
            // -------------------------------------------------

            const maxSize =
                10 * 1024 * 1024; // 10 MB


            if (file.size > maxSize) {

                alert(
                    "Image size must be less than 10 MB."
                );

                fileInput.value = "";

                if (selectedFile) {

                    selectedFile.textContent =
                        "No image selected";

                }

                return;

            }


            // -------------------------------------------------
            // SHOW FILE NAME
            // -------------------------------------------------

            if (selectedFile) {

                selectedFile.textContent =
                    "Selected: " + file.name;

            }


            // -------------------------------------------------
            // IMAGE PREVIEW
            // -------------------------------------------------

            showImagePreview(file);

        });

    }


    // =====================================================
    // IMAGE PREVIEW FUNCTION
    // =====================================================

    function showImagePreview(file) {

        const reader = new FileReader();


        reader.onload = function (event) {

            let preview =
                document.getElementById(
                    "imagePreview"
                );


            // If preview element doesn't exist,
            // create it.

            if (!preview) {

                preview =
                    document.createElement("img");

                preview.id =
                    "imagePreview";

                preview.style.width =
                    "100%";

                preview.style.maxWidth =
                    "400px";

                preview.style.maxHeight =
                    "400px";

                preview.style.objectFit =
                    "cover";

                preview.style.borderRadius =
                    "15px";

                preview.style.marginTop =
                    "20px";


                if (fileInput.parentElement) {

                    fileInput.parentElement.appendChild(
                        preview
                    );

                }

            }


            preview.src =
                event.target.result;

        };


        reader.readAsDataURL(file);

    }


    // =====================================================
    // FORM VALIDATION
    // =====================================================

    const form =
        fileInput
        ? fileInput.closest("form")
        : null;


    if (form) {

        form.addEventListener(
            "submit",
            function (event) {

                if (
                    !fileInput ||
                    fileInput.files.length === 0
                ) {

                    event.preventDefault();

                    alert(
                        "Please select a plant leaf image first."
                    );

                    return;

                }


                const file =
                    fileInput.files[0];


                if (!file.type.startsWith("image/")) {

                    event.preventDefault();

                    alert(
                        "Please select a valid image."
                    );

                    return;

                }


                // -------------------------------------------------
                // SHOW ANALYZING MESSAGE
                // -------------------------------------------------

                const analyzeButton =
                    form.querySelector(
                        'button[type="submit"]'
                    );


                if (analyzeButton) {

                    analyzeButton.disabled =
                        true;

                    analyzeButton.innerText =
                        "Analyzing...";

                }

            }
        );

    }

});

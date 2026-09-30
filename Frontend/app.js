const imageInput = document.getElementById("imageInput");
const fileName = document.getElementById("fileName");
const uploadButton = document.getElementById("uploadButton");
const status = document.getElementById("status");

let selectedFile = null;


// Image select hone par
imageInput.addEventListener("change", () => {

    selectedFile = imageInput.files[0];

    if (!selectedFile) {
        fileName.textContent = "No file selected";
        uploadButton.disabled = true;
        return;
    }

    fileName.textContent = selectedFile.name;
    uploadButton.disabled = false;
    status.textContent = "";
});


// Processing result wait karna
async function waitForResult(imageId) {

    const RESULT_API =
        "https://yykukhyo3g.execute-api.ap-south-1.amazonaws.com/result";

    const maxAttempts = 20;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {

        try {

            const response = await fetch(
                `${RESULT_API}?id=${encodeURIComponent(imageId)}`
            );

            if (response.ok) {

                const data = await response.json();

                console.log("Processing result:", data);

                return data;
            }

        } catch (error) {

            console.log(
                `Result check ${attempt} failed:`,
                error
            );
        }

        status.textContent =
            `Processing image... (${attempt}/${maxAttempts})`;

        await new Promise(resolve =>
            setTimeout(resolve, 2000)
        );
    }

    throw new Error("Processing timed out");
}


// Upload button
uploadButton.addEventListener("click", async () => {

    if (!selectedFile) {
        return;
    }

    uploadButton.disabled = true;

    status.textContent = "Preparing upload...";

    try {

        const API_URL =
            "https://yykukhyo3g.execute-api.ap-south-1.amazonaws.com/upload";


        // 1. Presigned URL request
        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                filename: selectedFile.name,
                contentType: selectedFile.type
            })
        });


        if (!response.ok) {
            throw new Error(
                "Could not generate upload URL"
            );
        }


        const data = await response.json();

        console.log("Upload API response:", data);


        // 2. Direct S3 upload
        status.textContent = "Uploading image...";


        const uploadResponse = await fetch(
            data.uploadUrl,
            {
                method: "PUT",

                headers: {
                    "Content-Type": selectedFile.type
                },

                body: selectedFile
            }
        );


        if (!uploadResponse.ok) {

            const errorText =
                await uploadResponse.text();

            console.error(
                "S3 upload error:",
                errorText
            );

            throw new Error(
                `S3 upload failed: ${uploadResponse.status}`
            );
        }


        status.textContent =
            "✓ Image uploaded successfully. Processing...";


        // 3. Image ID
        const imageId =
            data.image_id ||
            data.imageId;


        if (!imageId) {

            console.error(
                "Upload API response missing image ID:",
                data
            );

            throw new Error(
                "Image ID was not returned by upload API"
            );
        }


        // 4. Wait for Lambda processing
        const result =
            await waitForResult(imageId);


        // 5. Thumbnail URL
        const thumbnailUrl = result.thumbnail_url;


        console.log(
            "Thumbnail URL:",
            thumbnailUrl
        );


        // 6. Thumbnail display
        showThumbnail(
            thumbnailUrl,
            result
        );


        status.textContent =
            "✓ Processing complete!";


    } catch (error) {

        console.error(error);

        status.textContent =
            "✕ " + error.message;

    } finally {

        uploadButton.disabled = false;
    }
});


// Thumbnail UI
function showThumbnail(thumbnailUrl, result) {

    let preview = document.getElementById(
        "thumbnailPreview"
    );

    if (!preview) {

        preview = document.createElement("div");

        preview.id = "thumbnailPreview";

        preview.style.marginTop = "24px";

        uploadButton.parentElement.appendChild(
            preview
        );
    }


    preview.innerHTML = `

        <div style="
            margin-top: 20px;
            padding: 20px;
            border-radius: 16px;
            background: #111827;
            border: 1px solid #374151;
        ">

            <h3 style="
                color: white;
                margin-bottom: 15px;
            ">
                Thumbnail Ready ✓
            </h3>

            <img
                src="${thumbnailUrl}"
                alt="Generated thumbnail"
                style="
                    max-width: 300px;
                    max-height: 300px;
                    border-radius: 12px;
                    display: block;
                    margin: 0 auto 15px;
                "
            >

            <p style="color: #9ca3af;">
                ${result.filename}
            </p>

            <p style="color: #9ca3af;">
                Original: ${result.original_width}
                ×
                ${result.original_height}
            </p>

        </div>
    `;
}

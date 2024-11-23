// Wait for the DOM to fully load
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const resultsDiv = document.getElementById("results");

    // Add event listener to the form
    form.addEventListener("submit", async (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Gather form data
        const formData = new FormData(form);
        const formObject = {};
        formData.forEach((value, key) => {
            formObject[key] = value;
        });

        // Send the form data to the server using Fetch API
        try {
            const response = await fetch("/results", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formObject),
            });

            if (response.ok) {
                const data = await response.json();
                displayRecommendations(data.recommendations);
            } else {
                console.error("Error with the request:", response.statusText);
                resultsDiv.innerHTML = `<p class="error">Something went wrong. Please try again.</p>`;
            }
        } catch (error) {
            console.error("Fetch error:", error);
            resultsDiv.innerHTML = `<p class="error">Failed to connect to the server. Please try again later.</p>`;
        }
    });

    // Function to display recommendations on the page
    function displayRecommendations(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            resultsDiv.innerHTML = `<p>No recommendations found for your input.</p>`;
            return;
        }

        const list = document.createElement("ul");
        recommendations.forEach((rec) => {
            const listItem = document.createElement("li");
            listItem.textContent = rec;
            list.appendChild(listItem);
        });

        resultsDiv.innerHTML = `<h2>Recommended Content:</h2>`;
        resultsDiv.appendChild(list);
    }
});
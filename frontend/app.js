
const API_URL = "http://127.0.0.1:8000";

// Find the HTML elements we'll interact with
const searchForm = document.getElementById("search-form");
const resultsSection = document.getElementById("results-section");
const strongMatches = document.getElementById("strong-matches");
const weakMatches = document.getElementById("weak-matches");
const noResults = document.getElementById("no-results");
const continueButton = document.getElementById("continue-button");

const addSection = document.getElementById("add-section");
const addForm = document.getElementById("add-form");
const submissionMessage = document.getElementById("submission-message");

// Display a list of matching books
function displayMatches(container, books) {
    container.replaceChildren();

    if (books.length === 0) {
        const message = document.createElement("p");
        message.textContent = "No matches in this category.";
        container.appendChild(message);
        return;
    }

    books.forEach(book => {
        const item = document.createElement("div");
        item.className = "book-result";

        const title = document.createElement("strong");
        title.textContent = book.title;

        const details = document.createElement("small");
        details.textContent =
            `${book.author} | ${book.language} | Bought by ${book.bought_by}`;

        item.append(title, details);
        container.appendChild(item);
    });
}

// Search for books using the GET endpoint
searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const title = document.getElementById("search-title").value.trim();
    const searchButton = searchForm.querySelector("button");

    if (title.length < 2) {
        alert("Please enter at least two characters.");
        return;
    }

    searchButton.disabled = true;
    resultsSection.classList.add("hidden");
    addSection.classList.add("hidden");

    const params = new URLSearchParams({
        q: title
    });

    try {
        const response = await fetch(
            `${API_URL}/books/search?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Search request failed.");
        }

        const data = await response.json();

        displayMatches(strongMatches, data.strong_matches);
        displayMatches(weakMatches, data.weak_matches);

        const totalMatches =
            data.strong_matches.length + data.weak_matches.length;

        noResults.classList.toggle("hidden", totalMatches > 0);
        resultsSection.classList.remove("hidden");

        // Prefill the add-book form
        document.getElementById("book-title").value = title;
        document.getElementById("book-author").value =
            document.getElementById("search-author").value.trim();
        document.getElementById("book-language").value = "English";

    } catch (error) {
        alert("Unable to search books. Please try again.");
        console.error(error);
    } finally {
        searchButton.disabled = false;
    }
});

// Show the add-book form after reviewing results
continueButton.addEventListener("click", () => {
    addSection.classList.remove("hidden");
    addSection.scrollIntoView({ behavior: "smooth" });
});

// Submit a new book using the POST endpoint
addForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const book = {
        title: document.getElementById("book-title").value.trim(),
        author: document.getElementById("book-author").value.trim(),
        language: document.getElementById("book-language").value,
        bought_by: document.getElementById("bought-by").value.trim()
    };

    const submitButton = addForm.querySelector("button");
    submitButton.disabled = true;
    submissionMessage.textContent = "Adding your book...";

    try {
        const response = await fetch(`${API_URL}/books`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(book)
        });

        if (response.status === 409) {
            submissionMessage.textContent =
                "This book is already on the list!";
            return;
        }

        if (!response.ok) {
            throw new Error("Unable to add book.");
        }

        submissionMessage.textContent =
            "Your book was added successfully!";

        addForm.reset();
        continueButton.disabled = true;

    } catch (error) {
        submissionMessage.textContent =
            "Something went wrong. Please try again.";
        console.error(error);
    } finally {
        submitButton.disabled = false;
    }
});

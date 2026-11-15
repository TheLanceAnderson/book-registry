
const API_URL = "https://book-registry-ov8k.onrender.com";

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

const confirmationSection = document.getElementById("confirmation-section");
const confirmSubmitButton = document.getElementById("confirm-submit-button");
const useOriginalButton = document.getElementById("use-original-button");
const cancelConfirmationButton = document.getElementById("cancel-confirmation-button");

let pendingBook = null;
let originalBook = null;

const FILLER_WORDS = new Set([
    // English
    "a", "an", "and", "as", "at", "by", "for",
    "from", "in", "into", "of", "on", "or",
    "the", "to", "with",

    // Spanish
    "a", "al", "de", "del", "el", "en", "la",
    "las", "los", "o", "para", "por", "un",
    "una", "unas", "unos", "y"
]);

function capitalizeWord(word) {
    return word
        .toLocaleLowerCase()
        .replace(
            /(^|[.'’\-])(\p{L})/gu,
            (match, prefix, letter) =>
                prefix + letter.toLocaleUpperCase()
        );
}

function properCaseTitle(text) {
    const words = text.trim().split(/\s+/);

    return words.map((word, index) => {
        const normalized = word
            .toLocaleLowerCase()
            .replace(/^[^\p{L}]+|[^\p{L}]+$/gu, "");

        const isFirst = index === 0;
        const isLast = index === words.length - 1;

        if (!isFirst && !isLast && FILLER_WORDS.has(normalized)) {
            return word.toLocaleLowerCase();
        }

        return capitalizeWord(word);
    }).join(" ");
}

function properCaseAuthor(text) {
    return text.trim()
        .split(/\s+/)
        .map(capitalizeWord)
        .join(" ");
}

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
    const author = document.getElementById("search-author").value.trim();
    const searchButton = searchForm.querySelector("button");

    if (title.length < 2) {
        alert("Please enter at least two characters.");
        return;
    }

    submissionMessage.textContent = "";
    searchButton.disabled = true;
    resultsSection.classList.add("hidden");
    addSection.classList.add("hidden");

    const params = new URLSearchParams({
        q: title
    });

    if (author) {
        params.append("author", author);
    }

    try {
        const response = await fetch(
            `${API_URL}/books/search?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Search request failed.");
        }

        const data = await response.json();

        const strongSection = document.getElementById("strong-section");
        const weakSection = document.getElementById("weak-section");

        strongSection.classList.toggle(
            "hidden",
            data.strong_matches.length === 0
        );

        weakSection.classList.toggle(
            "hidden",
            data.weak_matches.length === 0
        );

        const weakHeading = weakSection.querySelector("h3");

        weakHeading.textContent =
            data.strong_matches.length > 0
                ? "Other possible matches"
                : "Possible matches";

        if (data.strong_matches.length > 0) {
            displayMatches(strongMatches, data.strong_matches);
        }

        if (data.weak_matches.length > 0) {
            displayMatches(weakMatches, data.weak_matches);
        }

        const totalMatches =
            data.strong_matches.length + data.weak_matches.length;

        noResults.classList.toggle("hidden", totalMatches > 0);
        resultsSection.classList.remove("hidden");

        // Prefill the add-book form
        document.getElementById("book-title").value =
            properCaseTitle(title);

        document.getElementById("book-author").value =
            properCaseAuthor(author);

        document.getElementById("book-language").value =
            document.getElementById("search-language").value;

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
addForm.addEventListener("submit", (event) => {
    event.preventDefault();

    originalBook = {
        title: document.getElementById("book-title").value.trim(),
        author: document.getElementById("book-author").value.trim(),
        language: document.getElementById("book-language").value,
        bought_by: document.getElementById("bought-by").value.trim()
    };

    pendingBook = {
        ...originalBook,
        title: properCaseTitle(originalBook.title),
        author: properCaseAuthor(originalBook.author)
    };

    document.getElementById("preview-title").textContent =
        pendingBook.title;
    document.getElementById("preview-author").textContent =
        pendingBook.author;
    document.getElementById("preview-language").textContent =
        pendingBook.language;
    document.getElementById("preview-bought-by").textContent =
        pendingBook.bought_by;

    const hasChanges =
        pendingBook.title !== originalBook.title ||
        pendingBook.author !== originalBook.author;

    if (!hasChanges) {
        // No formatting changes needed: submit immediately
        confirmationSection.classList.add("hidden");
        submitBook(originalBook);
        return;
    }

    // Formatting changes detected: show confirmation
    useOriginalButton.classList.remove("hidden");

    confirmationSection.classList.remove("hidden");
    confirmationSection.scrollIntoView({ behavior: "smooth" });
});

cancelConfirmationButton.addEventListener("click", () => {
    confirmationSection.classList.add("hidden");
    pendingBook = null;
    originalBook = null;
});

// Send the selected version to the backend
async function submitBook(book) {
    confirmSubmitButton.disabled = true;
    useOriginalButton.disabled = true;
    cancelConfirmationButton.disabled = true;
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

        confirmationSection.classList.add("hidden");
        addForm.reset();
        continueButton.disabled = true;
        pendingBook = null;
        originalBook = null;

    } catch (error) {
        submissionMessage.textContent =
            "Something went wrong. Please try again.";
        console.error(error);
    } finally {
        confirmSubmitButton.disabled = false;
        useOriginalButton.disabled = false;
        cancelConfirmationButton.disabled = false;
    }
}

confirmSubmitButton.addEventListener("click", () => {
    if (pendingBook) {
        submitBook(pendingBook);
    }
});

useOriginalButton.addEventListener("click", () => {
    if (originalBook) {
        submitBook(originalBook);
    }
});

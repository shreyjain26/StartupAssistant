// Hide the loading spinner on page load
window.addEventListener("load", () => {
    document.getElementById("loading").classList.add("hidden");
});

// Replace with your Google Gemini API Key
const GOOGLE_API_KEY = "AIzaSyDchPHXugkL3oGNHSYT7xG5ThJ2_x_ItSc";
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key=" + GOOGLE_API_KEY;

// Replace with your Serper API Key
const SERPER_API_KEY = "06c9780f1982684a8710476b812e5a90bdb0be2b"; // Sign up at https://serper.dev/
const SERPER_API_URL = "https://google.serper.dev/search";

// Convert feasibility score (0-100) to star rating (1-5 stars)
function scoreToStars(score) {
    return "★".repeat(Math.round(score / 20)) + "☆".repeat(5 - Math.round(score / 20));
}

// Hide the loading spinner on page load
window.addEventListener("load", () => {
    document.getElementById("loading").classList.add("hidden");
});

// Function to show loading spinner
function showLoading() {
    const loadingSpinner = document.getElementById("loading");
    loadingSpinner.classList.remove("hidden");
    loadingSpinner.style.display = "flex"; // Set display to flex
}

// Function to hide loading spinner
function hideLoading() {
    const loadingSpinner = document.getElementById("loading");
    loadingSpinner.classList.add("hidden");
    loadingSpinner.style.display = "none"; // Set display to none
}

// Function to fetch competition search results using Serper API
async function fetchCompetitionSearchResults(query) {
    const requestData = {
        q: query,
        gl: "us", // Country code (optional)
        hl: "en", // Language (optional)
        num: 5 // Number of results to fetch
    };

    try {
        const response = await fetch(SERPER_API_URL, {
            method: "POST",
            headers: {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        return data.organic; // Return the organic search results
    } catch (error) {
        console.error("Error fetching competition search results:", error);
        return null;
    }
}

// Function to generate a refined search query
function generateSearchQuery(description, industry, target_market, problem, fallback = false) {
    if (fallback) {
        // Fallback query for similar options
        return `similar options to "${description}" in ${industry} for ${target_market} solving ${problem}`;
    }
    // Primary query for competitors
    return `competitors of "${description}" in ${industry} for ${target_market} solving ${problem}`;
}

// Function to display competition search results
function displayCompetitionResults(results, isFallback = false) {
    const searchResultsContainer = document.getElementById("search-results");
    searchResultsContainer.innerHTML = ""; // Clear previous results

    if (!results || results.length === 0) {
        if (isFallback) {
            searchResultsContainer.innerHTML = "<p>No similar options found.</p>";
        } else {
            searchResultsContainer.innerHTML = "<p>No competitors found. Searching for similar options...</p>";
        }
        return;
    }

    results.forEach(result => {
        const resultCard = document.createElement("div");
        resultCard.classList.add("search-result-card");

        resultCard.innerHTML = `
            <h3>${result.title}</h3>
            <p>${result.snippet}</p>
            <p><a href="${result.link}" target="_blank">Visit Website</a></p>
        `;

        searchResultsContainer.appendChild(resultCard);
    });

    document.getElementById("competition-results").classList.remove("hidden");
}

// Main function to analyze the business idea
async function analyzeIdea() {
    const description = document.getElementById("description").value;
    const industry = document.getElementById("industry").value;
    const target_market = document.getElementById("target_market").value;
    const usp = document.getElementById("usp").value;
    const problem = document.getElementById("problem").value;

    if (!description || !industry || !target_market || !usp || !problem) {
        alert("⚠ Please fill in all fields!");
        return;
    }

    // Show loading spinner
    showLoading();

    // Perform SWOT analysis
    const requestData = {
        "contents": [{
            "parts": [{
                "text": `
                Perform a SWOT analysis and assess the feasibility of the following business idea.
                Provide ONLY a JSON output with these fields:

                {
                    "strengths": ["List key strengths"],
                    "weaknesses": ["List key weaknesses"],
                    "opportunities": ["List opportunities for growth and expansion"],
                    "threats": ["List potential threats and challenges"],
                    "feasibility_score": "A numerical score between 0 and 100 indicating feasibility",
                    "reasoning": "Brief explanation of the feasibility score"
                }

                Description: ${description}
                Industry: ${industry}
                Target Market: ${target_market}
                Unique Selling Proposition (USP): ${usp}
                Problem Being Solved: ${problem}
                `
            }]
        }]
    };

    console.log("Request Data:", requestData); // Log the request payload

    try {
        // Fetch SWOT analysis from Gemini API
        const response = await fetch(GEMINI_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("API Response Data:", data); // Log the full response

        const textResponse = data.candidates[0].content.parts[0].text;
        console.log("Text Response:", textResponse); // Log the text response

        // Clean and parse the JSON response
        const cleanedResponse = textResponse.replace(/```json/g, "").replace(/```/g, "").trim();
        console.log("Cleaned Response:", cleanedResponse); // Log the cleaned response

        const jsonResponse = JSON.parse(cleanedResponse);
        console.log("Parsed JSON Response:", jsonResponse); // Log the parsed JSON

        // Display SWOT analysis results
        document.getElementById("feasibility_score").innerHTML = `⭐ Feasibility Score: ${jsonResponse.feasibility_score}/100 (${scoreToStars(jsonResponse.feasibility_score)})`;
        document.getElementById("reasoning").textContent = `📌 ${jsonResponse.reasoning}`;
        document.getElementById("strengths").innerHTML = jsonResponse.strengths.map(s => `<li>${s}</li>`).join('');
        document.getElementById("weaknesses").innerHTML = jsonResponse.weaknesses.map(w => `<li>${w}</li>`).join('');
        document.getElementById("opportunities").innerHTML = jsonResponse.opportunities.map(o => `<li>${o}</li>`).join('');
        document.getElementById("threats").innerHTML = jsonResponse.threats.map(t => `<li>${t}</li>`).join('');

        document.getElementById("output").classList.remove("hidden");

        // Generate a refined search query for competition analysis
        let searchQuery = generateSearchQuery(description, industry, target_market, problem);
        console.log("Search Query:", searchQuery); // Log the search query

        // Fetch competition search results
        let competitionResults = await fetchCompetitionSearchResults(searchQuery);

        if (!competitionResults || competitionResults.length === 0) {
            // If no competitors found, search for similar options
            searchQuery = generateSearchQuery(description, industry, target_market, problem, true);
            console.log("Fallback Search Query:", searchQuery); // Log the fallback query
            competitionResults = await fetchCompetitionSearchResults(searchQuery);
            displayCompetitionResults(competitionResults, true); // Display similar options
        } else {
            displayCompetitionResults(competitionResults); // Display competitors
        }
    } catch (error) {
        console.error("Error:", error);
        alert("⚠ An error occurred. Please check the console for details.");
    } 

    // Simulate a delay for demonstration purposes
    setTimeout(() => {
        // Hide loading spinner after analysis is complete
        hideLoading();
    }, 3000); // Replace this with your actual API call logic
}
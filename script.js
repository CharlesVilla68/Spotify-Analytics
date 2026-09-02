const limitSelect = document.getElementById("limit-select");
const allTimeCheckbox = document.getElementById("all-time-checkbox");
const amountInput = document.getElementById("amount-input");
const unitSelect = document.getElementById("unit-select");
const resultsBody = document.getElementById("results-body");
const resultsHead = document.getElementById("results-head");
const pageTitle = document.getElementById("page-title");
const tabTracks = document.getElementById("tab-tracks");
const tabGenres = document.getElementById("tab-genres");

let activeView = "tracks";

function setActiveTab(view) {
  activeView = view;

  tabTracks.classList.toggle("active", view === "tracks");
  tabGenres.classList.toggle("active", view === "genres");

  if (view === "tracks") {
    pageTitle.textContent = "Top Tracks";
    resultsHead.innerHTML = `
            <tr>
                <th>Track</th>
                <th>Artist</th>
                <th>Plays</th>
            </tr>
        `;
  } else {
    pageTitle.textContent = "Top Genres";
    resultsHead.innerHTML = `
            <tr>
                <th>Genre</th>
                <th>Plays</th>
            </tr>
        `;
  }

  loadResults();
}

function loadResults() {
  const limit = limitSelect.value;
  const endpoint = activeView === "tracks" ? "top-tracks" : "top-genres";

  let url = `http://127.0.0.1:5001/api/${endpoint}?limit=${limit}`;

  if (!allTimeCheckbox.checked) {
    const amount = amountInput.value;
    const unit = unitSelect.value;
    url += `&amount=${amount}&unit=${unit}`;
  }

  fetch(url)
    .then((response) => response.json())
    .then((rows) => {
      resultsBody.innerHTML = "";

      rows.forEach((row) => {
        const tr = document.createElement("tr");

        if (activeView === "tracks") {
          tr.innerHTML = `
                        <td>${row.track_name}</td>
                        <td>${row.artist_name}</td>
                        <td>${row.play_count}</td>
                    `;
        } else {
          tr.innerHTML = `
                        <td>${row.genre}</td>
                        <td>${row.play_count}</td>
                    `;
        }

        resultsBody.appendChild(tr);
      });
    });
}

allTimeCheckbox.addEventListener("change", () => {
  const disabled = allTimeCheckbox.checked;
  amountInput.disabled = disabled;
  unitSelect.disabled = disabled;
  loadResults();
});

amountInput.addEventListener("change", loadResults);
unitSelect.addEventListener("change", loadResults);
tabTracks.addEventListener("click", () => setActiveTab("tracks"));
tabGenres.addEventListener("click", () => setActiveTab("genres"));
limitSelect.addEventListener("change", loadResults);

loadResults();

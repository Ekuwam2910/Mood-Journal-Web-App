const $ = (sel) => document.querySelector(sel);

const form = $("#entry-form");
const textarea = $("#entry-text");
const statusEl = $("#status");
const listEl = $("#entries-list");

let chart;
let chartData = {
  labels: [],
  datasets: [{
    label: "Mood score (0..1)",
    data: [],
    tension: 0.25
  }]
};

function renderChart() {
  const ctx = document.getElementById("moodChart").getContext("2d");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: chartData,
    options: {
      responsive: true,
      scales: {
        y: { min: 0, max: 1 }
      }
    }
  });
}

async function fetchEntries() {
  const res = await fetch("/api/entries");
  const data = await res.json();
  listEl.innerHTML = "";
  chartData.labels = [];
  chartData.datasets[0].data = [];

  data.forEach(e => {
    const li = document.createElement("li");
    const left = document.createElement("div");
    const right = document.createElement("div");

    left.innerHTML = `<strong>${e.mood_label}</strong> • score ${e.mood_score.toFixed(2)}<br>
      <span class="meta">${new Date(e.created_at).toLocaleString()}</span><br>${e.text}`;

    const del = document.createElement("button");
    del.textContent = "Delete";
    del.onclick = () => deleteEntry(e.id);

    right.appendChild(del);
    li.appendChild(left);
    li.appendChild(right);
    listEl.appendChild(li);

    chartData.labels.push(new Date(e.created_at).toLocaleDateString());
    chartData.datasets[0].data.push(e.mood_score);
  });

  renderChart();
}

async function deleteEntry(id) {
  await fetch(`/api/entries/${id}`, { method: "DELETE" });
  await fetchEntries();
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = textarea.value.trim();
  if (!text) return;

  statusEl.textContent = "Analyzing...";
  try {
    const res = await fetch("/api/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (res.ok) {
      textarea.value = "";
      statusEl.textContent = `Saved as ${data.mood_label} (${data.mood_score.toFixed(2)})`;
      await fetchEntries();
    } else {
      statusEl.textContent = data.error || "Something went wrong.";
    }
  } catch (err) {
    statusEl.textContent = "Network error.";
  }
});

fetchEntries();

document.getElementById("uploadForm").addEventListener("submit", async function (e) {
    e.preventDefault();
  
    const fileInput = document.getElementById("fileInput");
    const loader = document.getElementById("loader");
    const summaryCards = document.getElementById("summaryCards");
    const dataPreview = document.getElementById("dataPreview");
    const numericPlots = document.getElementById("numericPlots");
    const catPlots = document.getElementById("catPlots");
    const corrHeatmap = document.getElementById("corrHeatmap");
    const corrBar = document.getElementById("corrBar");
    const missingHeatmap = document.getElementById("missingHeatmap");
  
    if (!fileInput.files.length) {
      alert("Please select a CSV file first!");
      return;
    }
  
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
  
    // Show loader
    loader.style.display = "block";
    summaryCards.innerHTML = "";
    dataPreview.innerHTML = "";
    numericPlots.innerHTML = "";
    catPlots.innerHTML = "";
    corrHeatmap.innerHTML = "";
    corrBar.innerHTML = "";
    missingHeatmap.innerHTML = "";
  
    try {
      const response = await fetch("/upload", { method: "POST", body: formData });
      const data = await response.json();
      loader.style.display = "none";
  
      if (!data.success) {
        alert("Error: " + data.error);
        return;
      }
  
      // ✅ Summary Cards
      summaryCards.innerHTML = `
        <div class="col-md-3"><div class="card bg-dark p-3 text-center"><h5>Rows</h5><p>${data.summary.rows}</p></div></div>
        <div class="col-md-3"><div class="card bg-dark p-3 text-center"><h5>Columns</h5><p>${data.summary.columns}</p></div></div>
        <div class="col-md-3"><div class="card bg-dark p-3 text-center"><h5>Missing Values</h5><p>${data.summary.missing}</p></div></div>
        <div class="col-md-3"><div class="card bg-dark p-3 text-center"><h5>Duplicates</h5><p>${data.summary.duplicates}</p></div></div>
      `;
  
      // ✅ Data Preview
      if (data.preview_html) {
        dataPreview.innerHTML = `<h5 class="mb-2">Data Preview</h5>${data.preview_html}`;
      }
  
      // ✅ Missing Heatmap
      if (data.missing_heatmap) {
        Plotly.newPlot("missingHeatmap", data.missing_heatmap.data, data.missing_heatmap.layout);
      }
  
      // ✅ Numeric Plots
      if (data.numeric && data.numeric.length > 0) {
        data.numeric.forEach(col => {
          const div = document.createElement("div");
          div.classList.add("p-2", "bg-dark", "rounded");
          div.style.width = "45%";
          numericPlots.appendChild(div);
  
          Plotly.newPlot(div, [{
            x: col.values,
            type: "histogram",
            marker: { color: "#0d6efd" }
          }], {
            title: col.column,
            paper_bgcolor: "#212529",
            plot_bgcolor: "#212529",
            font: { color: "white" },
          });
        });
      } else {
        numericPlots.innerHTML = "<p>No numeric columns detected.</p>";
      }
  
      // ✅ Categorical Plots
      if (data.categorical && data.categorical.length > 0) {
        data.categorical.forEach(col => {
          const div = document.createElement("div");
          div.classList.add("p-2", "bg-dark", "rounded");
          div.style.width = "45%";
          catPlots.appendChild(div);
  
          Plotly.newPlot(div, [{
            x: col.labels,
            y: col.counts,
            type: "bar",
            marker: { color: "#ffc107" }
          }], {
            title: col.column,
            paper_bgcolor: "#212529",
            plot_bgcolor: "#212529",
            font: { color: "white" },
          });
        });
      } else {
        catPlots.innerHTML = "<p>No categorical columns detected.</p>";
      }
  
      // ✅ Correlation Heatmap
      if (data.corr_heatmap) {
        Plotly.newPlot("corrHeatmap", data.corr_heatmap.data, data.corr_heatmap.layout);
      }
  
      // ✅ Correlation Bar (Top correlated features)
      if (data.corr_bar) {
        Plotly.newPlot("corrBar", data.corr_bar.data, data.corr_bar.layout);
      }
  
    } catch (err) {
      console.error("Error:", err);
      loader.style.display = "none";
      alert("An error occurred while processing the file.");
    }
  });
  
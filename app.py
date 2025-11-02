from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
import io, os, base64, json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- utilities ----------
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def convert(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Series, pd.DataFrame)):
        return obj.to_dict()
    return obj


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "error": "no file uploaded"}), 400

    # --- read dataset safely ---
    try:
        df = pd.read_csv(file, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, encoding="latin1")
        except Exception:
            # optional: handle Excel files too
            if file.filename.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(file)
            else:
                return jsonify({"success": False, "error": "Unsupported or corrupted file encoding."}), 400



    # ---- basic summary ----
    summary = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing": f"{round(df.isnull().mean().mean() * 100, 2)}%",
        "duplicates": int(df.duplicated().sum()),
    }

    preview_html = df.head(10).to_html(classes="preview table table-striped table-dark", index=False)

    # ---- numeric summary ----
    num_df = df.select_dtypes(include=np.number)
    numeric = []
    for col in num_df.columns:
        values = num_df[col].dropna().tolist()
        numeric.append({
            "column": col,
            "values": values
        })

    # ---- categorical summary ----
    cat_df = df.select_dtypes(exclude=np.number)
    categorical = []
    for col in cat_df.columns:
        vc = cat_df[col].value_counts().head(5)
        categorical.append({
            "column": col,
            "labels": vc.index.tolist(),
            "counts": vc.values.tolist()
        })

    # ---- missing value heatmap ----
    missing_heatmap = None
    if df.isnull().sum().sum() > 0:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(df.isnull(), cbar=False, cmap="viridis")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        missing_heatmap = {
            "data": [{
                "z": [[1]],
                "type": "heatmap",
                "colorscale": "Viridis"
            }],
            "layout": {"title": "Missing Value Heatmap"}
        }

    # ---- correlation heatmap + bar ----
    corr_heatmap = None
    corr_bar = None
    if len(num_df.columns) > 1:
        corr = num_df.corr()

        # Heatmap
        fig = px.imshow(
            corr, text_auto=True, aspect="auto",
            title="Correlation Heatmap", color_continuous_scale="RdBu", template="plotly_dark"
        )
        corr_heatmap = json.loads(pio.to_json(fig))

        # Bar chart
        corr_pairs = corr.unstack().abs().sort_values(ascending=False)
        corr_pairs = corr_pairs[corr_pairs < 1].dropna().head(10).reset_index()
        corr_pairs.columns = ["Feature1", "Feature2", "Correlation"]
        fig2 = px.bar(
            corr_pairs, x="Correlation", y="Feature1",
            color="Correlation", orientation="h", template="plotly_dark",
            title="Top 10 Feature Correlations"
        )
        corr_bar = json.loads(pio.to_json(fig2))

    # ---- response ----
    result = {
        "success": True,
        "summary": summary,
        "preview_html": preview_html,
        "numeric": numeric,
        "categorical": categorical,
        "missing_heatmap": missing_heatmap,
        "corr_heatmap": corr_heatmap,
        "corr_bar": corr_bar
    }

    return jsonify(result)


@app.route("/download_summary")
def download_summary():
    path = os.path.join(UPLOAD_FOLDER, "eda_summary.csv")
    if not os.path.exists(path):
        return jsonify({"error": "no summary yet"}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

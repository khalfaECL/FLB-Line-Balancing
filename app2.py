from flask import Flask, render_template, request, send_file
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename

# Importer vos fonctions de traitement de mte4.py
from mte4 import (
    spt_balance_by_file,
    rpw_balance_by_file,
    mte_balance_by_file,
    generate_equilibrage_pdf_single_figure,
    plot_all_methods_by_file
)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

assignments = {}
fig = None
fig1 = None  # figure comparative à usage multiple

@app.route("/", methods=["GET", "POST"])
def index():
    global assignments, fig, fig1

    if request.method == "POST":
        method = request.form.get("method")
        files = request.files.getlist("excel_files")

        if not method or not files:
            return render_template("index2.html", message="❌ Tous les champs sont requis.")

        try:
            for f in files:
                filename = secure_filename(f.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                f.save(filepath)

                # Appliquer les méthodes d’équilibrage
                spt_model = spt_balance_by_file(filepath)
                rpw_model = rpw_balance_by_file(filepath)
                mte_model = mte_balance_by_file(filepath)

                assignments = {
                    "SPT": (spt_model["ws"], spt_model["wst"]),
                    "RPW": (rpw_model["ws"], rpw_model["wst"]),
                    "MTE": (mte_model["ws"], mte_model["wst"])
                }

                # Sélection de la méthode demandée
                result_model = {"SPT": spt_model, "RPW": rpw_model, "MTE": mte_model}[method]
                fig = result_model["fig"]
                kpis = result_model["kpis"]

                # Générer la figure comparative
                fig1 = plot_all_methods_by_file(filepath)

                # Enregistrer les graphiques
                fig_path = os.path.join("static", "figure.png")
                fig1_path = os.path.join("static", "figure1.png")
                fig.savefig(fig_path)
                fig1.savefig(fig1_path)
                plt.close(fig)
                plt.close(fig1)

                return render_template("index2.html", message="✅ Équilibrage terminé", fig_path=fig_path, fig1_path=fig1_path, kpis=kpis)

        except Exception as e:
            return render_template("index2.html", message=f"❌ Une erreur est survenue : {e}")

    return render_template("index2.html")

@app.route("/download")
def download_pdf():
    global fig1, assignments

    if fig1 is None or not assignments:
        return "❌ Aucun rapport disponible à télécharger."

    try:
        output_path = os.path.join(OUTPUT_FOLDER, "rapport_equilibrage.pdf")
        generate_equilibrage_pdf_single_figure(fig1, assignments, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return f"❌ Erreur lors de la génération du PDF : {e}"

if __name__ == "__main__":
    app.run(debug=True)

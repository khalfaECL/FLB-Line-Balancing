from flask import Flask, render_template, request, send_file
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
from io import BytesIO

# Importer les fonctions depuis ton notebook (converties en .py ou copiées ici)
from mte4 import (
    spt_balance_by_file,
    rpw_balance_by_file,
    mte_balance_by_file,
    generate_equilibrage_pdf_single_figure,
    plot_all_methods_by_file
)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

assignments = {}
fig = None
@app.route("/",methods=["POST"])
def test():
    return "<h1> Ça marche ✅</h1>"
@app.route("/home", methods=["GET", "POST"])
def index():
    global assignments, fig

    if request.method == "POST":
        method = request.form["method"]
        files = request.files.getlist("excel_files")

        if not files:
            return render_template("index.html", message="Aucun fichier sélectionné")

        filepaths = []
        for f in files:
            filename = secure_filename(f.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(filepath)
            filepaths.append(filepath)

        # Un seul fichier traité à la fois pour simplicité
        file = filepaths[0]
        spt_model = spt_balance_by_file(file)
        rpw_model = rpw_balance_by_file(file)
        mte_model = mte_balance_by_file(file)

        assignments = {
            "SPT": (spt_model["ws"], spt_model["wst"]),
            "RPW": (rpw_model["ws"], rpw_model["wst"]),
            "MTE": (mte_model["ws"], mte_model["wst"])
        }
        fig1=plot_all_methods_by_file(filepath)
        result_model = {"SPT": spt_model, "RPW": rpw_model, "MTE": mte_model}[method]
        fig = result_model["fig"]

        # Sauvegarder la figure temporairement
        fig_path = os.path.join("static", "figure.png")
        fig.savefig(fig_path)
        fig1_path=os.path.join("static", "figure1.png")
        fig1.savefig(fig1_path)
        plt.close(fig)
        plt.close(fig1)

        return render_template("index.html", message="Équilibrage effectué", fig_path=fig_path)

    return render_template("index.html")

@app.route("/download")
def download_pdf():
    global fig1, fig,assignments

    if fig is None or not assignments:
        return "Aucun équilibrage effectué"

    output_path = "output/rapport_equilibrage.pdf"
    os.makedirs("output", exist_ok=True)
    
    generate_equilibrage_pdf_single_figure(fig1, assignments, output_path)

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

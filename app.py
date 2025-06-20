from flask import Flask, render_template, request
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage

# 📦 Importer les fonctions de traitement
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

# ✅ Paramètres Gmail (utilise un mot de passe d'application)
GMAIL_ADDRESS = "jose5alfa18@gmail.com"  # Remplace ici
GMAIL_APP_PASSWORD = "ewad dvhm mfak zpdh"  # Mot de passe application à 16 chiffres

def envoyer_email_gmail(destinataire, fichier_pdf):
    msg = EmailMessage()
    msg["Subject"] = "📊 Rapport d’équilibrage"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = destinataire
    msg.set_content("Bonjour,\n\nVeuillez trouver en pièce jointe le rapport d’équilibrage demandé.\n\nCordialement,\nL’équipe MTE")

    with open(fichier_pdf, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="rapport_equilibrage.pdf")

    # Envoi via Gmail
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        method = request.form.get("method")
        email = request.form.get("client_email")
        files = request.files.getlist("excel_files")

        if not method or not email or not files:
            return render_template("index.html", message="❌ Tous les champs sont requis.")

        try:
            for f in files:
                filename = secure_filename(f.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                f.save(path)

                # Appliquer les méthodes
                spt_model = spt_balance_by_file(path)
                rpw_model = rpw_balance_by_file(path)
                mte_model = mte_balance_by_file(path)

                assignments = {
                    "SPT": (spt_model["ws"], spt_model["wst"]),
                    "RPW": (rpw_model["ws"], rpw_model["wst"]),
                    "MTE": (mte_model["ws"], mte_model["wst"])
                }

                fig = plot_all_methods_by_file(path)
                pdf_path = os.path.join(OUTPUT_FOLDER, f"rapport_{filename}.pdf")
                generate_equilibrage_pdf_single_figure(fig, assignments, pdf_path)
                plt.close(fig)

                envoyer_email_gmail(email, pdf_path)

            return render_template("index.html", message=f"✅ Rapport envoyé à {email}")

        except Exception as e:
            return render_template("index.html", message=f"❌ Erreur pendant le traitement : {e}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

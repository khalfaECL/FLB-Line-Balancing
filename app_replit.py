# app.py
from flask import Flask, render_template, request, send_file
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage
import csv
from datetime import datetime
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

GMAIL_ADDRESS = "jose5alfa18@gmail.com"
GMAIL_APP_PASSWORD = "bokh utph zhtl ivqp"

def envoyer_email_gmail(destinataire, fichier_pdf):
    msg = EmailMessage()
    msg["Subject"] = "📊 Rapport d’équilibrage"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = destinataire
    msg.set_content("Bonjour,\n\nVeuillez trouver en pièce jointe le rapport d’équilibrage demandé.\n\nCordialement,\nL’équipe MTE")

    with open(fichier_pdf, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="rapport_equilibrage.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

ADMIN_CSV = "demandes.csv"


def lire_demandes():
    if not os.path.exists(ADMIN_CSV):
        return []
    with open(ADMIN_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

@app.route("/admin")
def admin_dashboard():
    demandes = lire_demandes()
    return render_template("admin2.html", demandes=demandes)

@app.route("/admin/download/<pdf_name>")
def download_pdf_admin(pdf_name):
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_name)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return f"❌ Fichier {pdf_name} introuvable.", 404

@app.route("/admin/send/<int:index>")
def envoyer_depuis_admin(index):
    demandes = lire_demandes()
    if index >= len(demandes):
        return "❌ Demande non trouvée", 404

    ligne = demandes[index]
    email = ligne["email"]
    pdf = ligne["pdf"]
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf)

    try:
        envoyer_email_gmail(email, pdf_path)
        demandes[index]["statut"] = "Envoyé"
        with open("demandes.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "email", "fichier", "methode", "statut", "pdf"])
            writer.writeheader()
            writer.writerows(demandes)

        return f"✅ Rapport envoyé à {email} ! <a href='/admin'>Retour</a>"
    except Exception as e:
        return f"❌ Erreur lors de l'envoi : {e}"

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

                with open("demandes.csv", "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["date", "email", "fichier", "methode", "statut", "pdf"])
                    if f.tell() == 0:
                        writer.writeheader()
                    writer.writerow({
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "email": email,
                        "fichier": filename,
                        "methode": method,
                        "statut": "En attente",
                        "pdf": f"rapport_{filename}.pdf"
                    })

            return render_template("index.html", message="✅ Demande envoyée. En attente de réponse. Veuillez vérifier votre boîte mail.")
        except Exception as e:
            return render_template("index.html", message=f"❌ Erreur pendant le traitement : {e}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

import base64
import os
from email.mime.text import MIMEText
import tempfile

from googleapiclient.discovery import build
from langchain_core.tools import tool
from langchain_google_community._utils import get_google_credentials

from tools.clients import get_client_by_email
import json
from google.oauth2 import service_account
import resend 
resend.api_key = os.environ["RESEND_API_KEY"]

BASE_DIR = __import__("pathlib").Path(__file__).resolve().parents[2]
TOKEN_FILE = BASE_DIR / "token.json"


def _get_client_secrets_file() -> str:
    encoded_credentials = os.getenv("GOOGLE_CREDENTIALS_BASE64", "").strip()
    if not encoded_credentials:
        raise RuntimeError(
            "La variable d'environnement GOOGLE_CREDENTIALS_BASE64 n'est pas définie."
        )

    decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_file.write(decoded_credentials)
        return temp_file.name

def _get_service_account_info() -> dict:
    encoded_credentials = os.getenv("GOOGLE_CREDENTIALS_BASE64", "").strip()
    if not encoded_credentials:
        raise RuntimeError(
            "La variable d'environnement GOOGLE_CREDENTIALS_BASE64 n'est pas définie."
        )

    decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
    return json.loads(decoded_credentials)


@tool
def send_confirmation_email(to_email: str, date_rdv: str, heure_rdv: str) -> str:
    """
    Utile pour envoyer un e-mail de confirmation au patient une fois que le rendez-vous est pris.
    Prend en paramètres l'adresse email du patient (to_email), la date et l'heure du rendez-vous.
    """
    try:
        # 1. Utilisation de la nouvelle fonction pour récupérer le client
        client_data = get_client_by_email(to_email)

        # On vérifie si le client a été trouvé ou s'il y a une erreur
        if "error" not in client_data:
            client_name = client_data.get("name", "Monsieur/Madame")
        else:
            client_name = "Monsieur/Madame"

        # # 2. Vérification des autorisations Google
        # credentials_info = _get_service_account_info()
        # credentials = service_account.Credentials.from_service_account_info(
        #     credentials_info,
        #     scopes=["https://www.googleapis.com/auth/gmail.send"],
        # )
        # service = build("gmail", "v1", credentials=credentials)

        # 3. Personnalisation et structure de l'e-mail
        subject = "Confirmation de votre rendez-vous - Clinique"
        body = (
            f"Bonjour {client_name},\n\n"
            f"Nous vous confirmons que votre rendez-vous a bien été enregistré "
            f"le {date_rdv} à {heure_rdv}.\n\n"
            f"--- Ceci est un message automatique, merci de ne pas y répondre ---\n\n"
            f"Cordialement,\n"
            f"Sophie, votre Secrétaire Médicale"
        )

        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject

        # Modifier le nom de l'expéditeur qui s'affiche dans la boîte du patient
        message["from"] = "Clinique (No-Reply) <me>"

        # Rediriger le bouton "Répondre" du patient vers une adresse invalide ou vide
        message["reply-to"] = "no-reply@clinique-annecy-fake-domain.com"

        # 4. Envoi via l'API Gmail
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_message = {"raw": raw_message}

        # service.users().messages().send(userId="me", body=send_message).execute()

        resend.Emails.send({
            "from": "Clinique <no-reply-clinique-annecy-fake-domain@resend.dev>",
            "to": to_email,
            "subject": "Confirmation de votre rendez-vous - Clinique",
            "text": body,   # 👈 SAME BODY, just sent as text email
        })
        return f"E-mail de confirmation envoyé avec succès à {client_name} ({to_email})."

    except Exception as e:
        print(f"DEBUG GMAIL ERROR: {str(e)}")
        return f"Erreur lors de l'envoi de l'e-mail : {str(e)}"

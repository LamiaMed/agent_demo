import base64
from email.mime.text import MIMEText
from pathlib import Path

from googleapiclient.discovery import build
from langchain_core.tools import tool
from langchain_google_community._utils import get_google_credentials

from backend.tools.clients import get_client_by_email

BASE_DIR = Path(__file__).resolve().parents[2]
TOKEN_FILE = BASE_DIR / "token.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"


@tool
def send_confirmation_email(to_email: str, date_rdv: str, heure_rdv: str) -> str:
    """
    Utile pour envoyer un e-mail de confirmation au patient une fois que le rendez-vous est pris.
    Prend en paramètres l'adresse email du patient (to_email), la date et l'heure du rendez-vous.
    """
    try:
        client_data = get_client_by_email(to_email)

        if "error" not in client_data:
            client_name = client_data.get("name", "Monsieur/Madame")
        else:
            client_name = "Monsieur/Madame"

        credentials = get_google_credentials(
            token_file=str(TOKEN_FILE),
            scopes=["https://www.googleapis.com/auth/gmail.send"],
            client_secrets_file=str(CREDENTIALS_FILE),
        )
        if credentials is None:
            return "Erreur : Les autorisations Google ne sont pas initialisées."
        service = build("gmail", "v1", credentials=credentials)

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

        message["from"] = "Clinique (No-Reply) <me>"

        message["reply-to"] = "no-reply@clinique-annecy-fake-domain.com"

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_message = {"raw": raw_message}

        service.users().messages().send(userId="me", body=send_message).execute()
        return f"E-mail de confirmation envoyé avec succès à {client_name} ({to_email})."

    except Exception as e:
        print(f"DEBUG GMAIL ERROR: {str(e)}")
        return f"Erreur lors de l'envoi de l'e-mail : {str(e)}"

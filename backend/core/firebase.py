import firebase_admin
from firebase_admin import credentials, auth
from core.config import settings

def initialize_firebase():

    if not settings.FIREBASE_PRIVATE_KEY:
        print("Firebase credentials not configured")
        return None

    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "token_uri": "https://oauth2.googleapis.com/token"
    })

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return auth
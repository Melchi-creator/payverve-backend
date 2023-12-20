from backend.core.utils import Constants
import firebase_admin
from firebase_admin import credentials

config = {
    "apiKey": Constants.WEB_API_KEY,
    "authDomain": "fireapp-c3e36.firebaseapp.com",
    "databaseURL": "https://fireapp-c3e36-default-rtdb.firebaseio.com",
    "projectId": Constants.PROJECT_ID,
    "storageBucket": "fireapp-c3e36.appspot.com",
    "messagingSenderId": "564960363824",
    "appId": Constants.APP_ID,
    "measurementId": "G-NBBM679DH2"
}

# cred = credentials.Certificate("path/to/serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

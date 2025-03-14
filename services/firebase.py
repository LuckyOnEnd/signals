import firebase_admin
import pyrebase
from fastapi import HTTPException
from firebase_admin import credentials, firestore

firebase_config = {
    "apiKey": "AIzaSyANTdHXlRmGlLdWNRrr00H8s4oYSnqGOAg",
    "authDomain": "primex-58365.firebaseapp.com",
    "projectId": "primex-58365",
    "storageBucket": "primex-58365.firebasestorage.app",
    "messagingSenderId": "233323718364",
    "appId": "1:233323718364:web:2b7321edabcbd50d96b619",
    "measurementId": "G-4RWTY2VMLL",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

cred = credentials.Certificate("primexalgo-3ea70-firebase-adminsdk-illnj-ee96014f0d.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def login_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        # doc_ref = db.collection("subscriptions").document(user['email'])
        # doc = doc_ref.get()

       # if doc.exists:
        if True:
            # data = doc.to_dict()
            # result = {
            #     'subscription_type': data['subscription_type'],
            #     'id': user['idToken'],
            # }
            return {"status": "success", "data": {
                'subscription_type': 'essential',
                'id': '123321123'
            }}
        else:
            raise HTTPException(status_code=404, detail="Subscription not found for this user")
    except Exception as e:
        raise e


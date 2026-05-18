import os
import flask
import requests
from flask import session, request, redirect
from google_auth_oauthlib.flow import Flow

# 1. הגדרות סביבה קריטיות לעבודה בתוך Codespaces
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# השורה הבאה מונעת את שגיאת ה-Mismatch ב-State שגורמת ל-500
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

# --- הגדרות ---
CLIENT_SECRETS_FILE = "client_secret.json"
PROJECT_ID = "ai-storypicser-496705"
REDIRECT_URI = 'https://jubilant-lamp-p7qgjxq9gqjcr4q5-8080.app.github.dev/callback'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

@app.route('/')
def index():
    return '<h1>Photo Story</h1><a href="/authorize">התחבר לגוגל פוטוס</a>'

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    
    # שימוש ב-state=None כדי למנוע את הקריסה ב-callback
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    session['code_verifier'] = flow.code_verifier
    return redirect(auth_url)

@app.route('/callback')
def callback():
    try:
        flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URI
        flow.code_verifier = session.get('code_verifier')
        
        # המרת הכתובת ל-HTTPS
        authorization_response = request.url.replace('http:', 'https:')
        
        # ניסיון שליפת הטוקן
        flow.fetch_token(authorization_response=authorization_response)
        session['token'] = flow.credentials.token
        
        return redirect('/scan')
    except Exception as e:
        # אם יש שגיאה, היא תודפס כאן במקום הודעת 500 כללית
        import traceback
        return f"<h2>קריסה ב-Callback:</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/scan')
def scan():
    token = session.get('token')
    if not token: return redirect('/authorize')

    url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Goog-User-Project': PROJECT_ID
    }
    
    # שליפת רשימת תמונות בסיסית
    response = requests.get(url, headers=headers, params={'pageSize': 50})
    
    if response.status_code != 200:
        return f"שגיאה {response.status_code}: {response.text}"
    
    data = response.json()
    items = data.get('mediaItems', [])
    
    res = "<h2>נמצאו תמונות:</h2><ul>"
    for item in items:
        res += f"<li>{item.get('filename')} - {item.get('mediaMetadata', {}).get('creationTime')}</li>"
    return res + "</ul>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

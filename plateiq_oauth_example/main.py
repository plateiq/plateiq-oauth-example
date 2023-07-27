import urllib
import requests
import os
from flask import Flask, redirect, url_for, session, abort, request
from functools import wraps

### CONFIG

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
PLATEIQ_AUTH_URL = os.environ.get("PLATEIQ_AUTH_URL", "https://login.plateiq.com")
PLATEIQ_API_URL = os.environ.get("PLATEIQ_API_URL", "https://api.qubiqle.com")
PLATEIQ_AUTH_CLIENT_ID = os.environ.get("PLATEIQ_AUTH_CLIENT_ID")
PLATEIQ_AUTH_CLIENT_SECRET = os.environ.get("PLATEIQ_AUTH_CLIENT_SECRET")
SECRET_KEY = os.environ.get("SECRET_KEY", "Notverysecretwhenlocal")


### FLASK APP
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


### AUTH


def login_required(f):
    """
    A decorator to require user login to access certain views.

    If a user isn't logged in they are redirected to the login
    screen.

    See: https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "email" not in session:
            session.clear()
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login")
def login():
    """
    We use Plate IQ's OAuth authentication system to handle auth and login.
    Redirect to the login page (generally login.plateiq.com) and then
    the auth system will redirect back to us with a code. We then change
    that code for an access token and we can access the API and know who
    the user is.
    """
    params = {
        "response_type": "code",
        "client_id": PLATEIQ_AUTH_CLIENT_ID,
        "redirect_uri": BASE_URL + url_for("oauth_login"),
    }
    url_parts = list(urllib.parse.urlparse(PLATEIQ_AUTH_URL + "/oauth/authorize/"))
    url_parts[4] = urllib.parse.urlencode(params)
    url = urllib.parse.urlunparse(url_parts)
    return redirect(url)


@app.route("/logout")
def logout():
    """
    Clear the user out of the session and global context variable,
    then redirect to the Plate IQ auth system's logout page.

    If we don't logout of Plate IQ's auth, the user will simply be
    automatically logged back in.
    """
    session.clear()
    return redirect(PLATEIQ_AUTH_URL + "/logout")


def login_the_user(access_token):
    user_response = requests.get(
        PLATEIQ_API_URL + "/auth/user",
        headers={"Authorization": "Bearer " + access_token},
    )

    if user_response.status_code != 200:
        abort(user_response.status_code)

    user = user_response.json()

    full_user_info = requests.get(
        user["url"], headers={"Authorization": "Bearer " + access_token}
    ).json()

    session.clear()

    session["email"] = user["email"]
    session["access_token"] = access_token

    return full_user_info


@app.route("/oauth/login")
def oauth_login():
    """
    This route handles the Plate IQ auth system callback. The auth
    system provides a code which we then call the auth system API
    with to receive an access token. That access token can be used
    to get the current user.
    """
    code = request.args.get("code")
    response = requests.post(
        PLATEIQ_AUTH_URL + "/oauth/token/",
        data={
            "code": code,
            "grant_type": "authorization_code",
            "client_id": PLATEIQ_AUTH_CLIENT_ID,
            "client_secret": PLATEIQ_AUTH_CLIENT_SECRET,
            "redirect_uri": BASE_URL + url_for("oauth_login"),
        },
    )

    if response.status_code != 200:
        abort(response.status_code)

    token = response.json()

    login_the_user(token["access_token"])

    return redirect(url_for("index"))


### END AUTH

@app.route("/")
@login_required
def index():
    return f"Hello, {session['email']}!"

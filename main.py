from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os

CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
TOKEN_INFO = ""

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")
app.config['SESSION_COOKIE_NAME'] = 'hdn97h6g8qfn72qh7h'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('mood', _external=True))


@app.route('/mood')
def mood():
    return render_template('mood.html')


@app.route('/create-playlist/<mood_status>')
def create_playlist(mood_status):
    try:
        token_info = get_token()
    except:
        return redirect(url_for("login", _external=False))
    sp = spotipy.Spotify(auth=token_info['access_token'])

    tracks = []

    top_artists = sp.current_user_top_artists()['items']
    artists = [artist['uri'] for artist in top_artists]

    results = []

    if mood_status == "happy":
        danceability = 1
        energy = 0.8
        valence = 1
        results = sp.recommendations(seed_artists=artists[:1], seed_genres=['happy', 'pop'],
                                     target_danceability=danceability,
                                     target_energy=energy,
                                     target_valence=valence)['tracks']
    elif mood_status == "sad":
        danceability = 0.2
        energy = 0.1
        valence = 0.1
        results = sp.recommendations(seed_artists=artists[:3],
                                     target_danceability=danceability,
                                     target_energy=energy,
                                     target_valence=valence)['tracks']
    elif mood_status == "angry":
        danceability = 0.8
        energy = 1
        valence = 0.1
        results = sp.recommendations(seed_artists=artists[:1], seed_genres=['rock'],
                                     target_danceability=danceability,
                                     target_energy=energy,
                                     target_valence=valence)['tracks']
    elif mood_status == "chill":
        danceability = 0.3
        energy = 0.3
        valence = 0.5
        results = sp.recommendations(seed_artists=artists[:1], seed_genres=['chill', 'r-n-b'],
                                     target_danceability=danceability,
                                     target_energy=energy,
                                     target_valence=valence)['tracks']

    for result in results:
        if not result['uri'] in tracks:
            tracks.append(result['uri'])

    playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=mood_status.title(), public=False,
                                       collaborative=False, description=f"{mood_status.title()} songs")
    playlist_id = playlist['id']
    sp.playlist_add_items(playlist_id=playlist_id, items=tracks)
    return render_template('success.html')


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=url_for('redirect_page', _external=True),
                        scope="playlist-modify-private user-top-read")


if __name__ == "__main__":
    app.run(debug=True)

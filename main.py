import os
from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
TOKEN_INFO = ""

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SESSION_COOKIE_NAME'] = 'nd8gq8f70h298un'


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
    if os.path.exists('.cache'):
        os.remove('.cache')
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('mood', _external=True))


@app.route('/mood')
def mood():
    return render_template('mood.html')


@app.route('/create-playlist', methods=["GET", "POST"])
def create_playlist():
    tracks = []

    try:
        token_info = get_token()
    except None:
        return redirect(url_for("login", _external=False))

    sp = spotipy.Spotify(auth=token_info['access_token'])

    top_artists = sp.current_user_top_artists()['items']
    artist_uris = [artist['uri'] for artist in top_artists]

    mood_status = request.form['mood-status'].lower()
    playlist_name = request.form['playlist-name']
    song_number = request.form['song-number']
    description = f"{mood_status.title()} songs"
    try:
        explicit_content = request.form['explicit']
    except KeyError:
        explicit_content = ""

    danceability = 0
    energy = 0
    valence = 0
    popularity = 0
    genres = []

    if mood_status == "happy":
        danceability = 0.8
        energy = 0.8
        valence = 1
        popularity = 90
        genres = ['happy', 'pop', 'road-trip', 'summer']
    elif mood_status == "sad":
        danceability = 0.1
        energy = 0.1
        valence = 0.1
        popularity = 90
        genres = ['sad', 'r-n-b', 'rainy-day', 'romance']
    elif mood_status == "angry":
        danceability = 0.5
        energy = 1
        valence = 0.1
        popularity = 80
        genres = ['emo', 'heavy-metal', 'rock', 'rock-n-roll']
    elif mood_status == "chill":
        danceability = 0.3
        energy = 0.3
        valence = 0.6
        popularity = 90
        genres = ['chill', 'r-n-b', 'rainy-day', 'house']
    elif mood_status == "party":
        danceability = 1
        energy = 1
        valence = 1
        popularity = 90
        genres = ['party', 'edm', 'dance', 'disco']

    results = sp.recommendations(seed_genres=genres,
                                 seed_artists=artist_uris[:1],
                                 target_danceability=danceability,
                                 target_energy=energy,
                                 target_valence=valence,
                                 target_popularity=popularity,
                                 limit=song_number)['tracks']

    for result in results:
        if not result['uri'] in tracks:
            if explicit_content == "true" or not result['explicit']:
                tracks.append(result['uri'])

    playlist_id = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name, public=False,
                                          collaborative=False, description=description)['id']
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
    app.run()

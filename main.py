import os
import requests
import base64
from flask import Flask, request

app = Flask(__name__)

# Spotify API credentials
CLIENT_ID = '6d5cbc6a56b547c7b960bad581ecbe29'
CLIENT_SECRET = '0989e2e553c74877b4896dc0b1f2ef78'

# Telegram Bot API Token
BOT_TOKEN = '7725996861:AAFvGCwWkTIr1wPVktG7rmr4Pqw-311MLJg'
CHAT_ID = '7124758066'

# Function to get Spotify API access token
def get_spotify_token():
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Error obtaining Spotify token:", response.json())
        return None

# Function to search for a song on Spotify
def search_spotify_song(song_name, token):
    url = f'https://api.spotify.com/v1/search?q={song_name}&type=track&limit=1'
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print("Error searching song on Spotify:", response.json())
        return None

# Function to send song details (including poster) to Telegram
def send_song_to_telegram(track_info, chat_id):
    # Extract song details
    photo_url = track_info['album']['images'][0]['url']  # Album image URL
    song_name = track_info['name']                       # Song name
    artist_name = track_info['artists'][0]['name']       # Artist name
    spotify_url = track_info['external_urls']['spotify'] # Spotify link
    
    # Telegram sendPhoto API URL
    telegram_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
    
    # Payload for sending photo with caption
    payload = {
        'chat_id': chat_id,
        'photo': photo_url,
        'caption': f"Song: {song_name}\nArtist: {artist_name}\n[Listen on Spotify]({spotify_url})",
        'parse_mode': 'Markdown'
    }
    
    # Send request to Telegram
    response = requests.post(telegram_url, data=payload)
    
    if response.status_code == 200:
        print("Song details sent to Telegram successfully!")
    else:
        print("Error sending message to Telegram:", response.json())

# Define a route for the Telegram webhook
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = request.get_json()
    
    # Check for a message in the update
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        song_name = update['message']['text']  # Get the song name from the message

        # Get Spotify API access token
        token = get_spotify_token()
        
        if token:
            # Search for the song
            song_data = search_spotify_song(song_name, token)
            
            if song_data and song_data['tracks']['items']:
                # Get the first track's details
                track_info = song_data['tracks']['items'][0]
                # Send the track details and poster to Telegram
                send_song_to_telegram(track_info, chat_id)
            else:
                send_song_to_telegram({"name": "Song not found", "artists": [{"name": "N/A"}], "album": {"images": [{"url": "https://via.placeholder.com/150"}]}}, chat_id)
        else:
            print("Failed to get Spotify token.")
    
    return '', 200  # Respond with HTTP 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

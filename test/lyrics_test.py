import requests

artist = "Meltt"
song = "The Fire"
url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={song}"
response = requests.get(url)
data = response.json()

print(data["plainLyrics"])

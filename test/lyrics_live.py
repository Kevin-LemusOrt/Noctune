from subprocess import check_output
import requests

song_data = check_output(
    ["playerctl", "metadata", "--format", "{{artist}} - {{title}}"]
).decode().strip()

parts = song_data.split(" - ")
artist = parts[0]
song = parts[1]

url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={song}"
response = requests.get(url)
data = response.json()

print(data["plainLyrics"])

import time

lyrics = """
[00:05.00] hello
[00:10.00] how are you
[00:15.00] goodbye
"""

lines = lyrics.strip().split("\n")
parsed_lyrics = []

for line in lines:
    timestamp = line.split("]")[0][1:]
    lyric = line.split("]")[1].strip()
    minutes = int(timestamp.split(":")[0])
    seconds = float(timestamp.split(":")[1])
    total_seconds = (minutes * 60) + seconds

    parsed_lyrics.append((total_seconds, lyric))

star_time = time.time()

show_index = -1

while True:
    current_time = time.time() - star_time

    for index, (timestamp, lyric) in enumerate(parsed_lyrics):

        if current_time >= timestamp and index > show_index:
            print(lyric)
            show_index = index
    
    time.sleep(0.1)
line = "[01:20.21] Hello world"

timestamp = line.split("]")[0][1:]
minutes = int(timestamp.split(":")[0])
seconds = float(timestamp.split(":")[1])
total_seconds = (minutes * 60) + seconds

print(round(total_seconds, 2))
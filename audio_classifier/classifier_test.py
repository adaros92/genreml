import subprocess

songs = ["https://www.youtube.com/watch?v=YrMQeEiK06k", "https://www.youtube.com/watch?v=WSeNSzJ2-Jw",
         "https://www.youtube.com/watch?v=8cb8ZUpAr94", "https://www.youtube.com/watch?v=v2AC41dglnM",
         "https://www.youtube.com/watch?v=wTRKAVbPbOY", "https://www.youtube.com/watch?v=OPf0YbXqDm0"]
file = open('predictions.csv', 'w+')
for song in songs:
    res = subprocess.run(["python3", "audio-classifier.py", "-y", song, "5"], capture_output=True, text=True)
    res_str = str(res.stderr)
    print(res_str)
    file.write(res_str + '\n')

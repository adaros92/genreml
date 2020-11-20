import subprocess

songs = ["https://www.youtube.com/watch?v=YrMQeEiK06k", "https://www.youtube.com/watch?v=WSeNSzJ2-Jw",
         "https://www.youtube.com/watch?v=8cb8ZUpAr94", "https://www.youtube.com/watch?v=v2AC41dglnM",
         "https://www.youtube.com/watch?v=wTRKAVbPbOY", "https://www.youtube.com/watch?v=OPf0YbXqDm0",
         "https://www.youtube.com/watch?v=WPefERS7EZs", "https://www.youtube.com/watch?v=fPr3yvkHYsE",
         "https://www.youtube.com/watch?v=UG3VcCAlUgE", "https://www.youtube.com/watch?v=HasaQvHCv4w",
         "https://www.youtube.com/watch?v=qN5zw04WxCc", "https://www.youtube.com/watch?v=RxabLA7UQ9k",
         "https://www.youtube.com/watch?v=hTWKbfoikeg", "https://www.youtube.com/watch?v=bx1Bh8ZvH84",
         "https://www.youtube.com/watch?v=YkgkThdzX-8", "https://www.youtube.com/watch?v=fKopy74weus",
         "https://www.youtube.com/watch?v=dvgZkm1xWPE", "https://www.youtube.com/watch?v=Zi_XLOBDo_Y",
         "https://www.youtube.com/watch?v=RUQl6YcMalg", "https://www.youtube.com/watch?v=ftjEcrrf7r0",
         "https://www.youtube.com/watch?v=fJ9rUzIMcZQ", "https://www.youtube.com/watch?v=A_MjCqQoLLA",
         "https://www.youtube.com/watch?v=1w7OgIMMRc4", "https://www.youtube.com/watch?v=e9BLw4W5KU8",
         "https://www.youtube.com/watch?v=xFrGuyw1V8s", "https://www.youtube.com/watch?v=Eab_beh07HU",
         "https://www.youtube.com/watch?v=3YxaaGgTQYM", "https://www.youtube.com/watch?v=WM8bTdBs-cw",
         "https://www.youtube.com/watch?v=RiJMwKdFJTI", "https://www.youtube.com/watch?v=QK8mJJJvaes",
         "https://www.youtube.com/watch?v=QGJuMBdaqIw", "https://www.youtube.com/watch?v=XbGs_qK2PQA",
         "https://www.youtube.com/watch?v=thIVtEOtlWM", "https://www.youtube.com/watch?v=_CL6n0FJZpk",
         "https://www.youtube.com/watch?v=PBwAxmrE194", "https://www.youtube.com/watch?v=aQkPcPqTq4M",
         "https://www.youtube.com/watch?v=rrVDATvUitA", "https://www.youtube.com/watch?v=9E6b3swbnWg",
         "https://www.youtube.com/watch?v=_D0ZQPqeJkk", "https://www.youtube.com/watch?v=-bTpp8PQSog",
         "https://www.youtube.com/watch?v=yydNF8tuVmU", "https://www.youtube.com/watch?v=x6QZn9xiuOE",
         "https://www.youtube.com/watch?v=86URGgqONvA", "https://www.youtube.com/watch?v=WGoDaYjdfSg",
         "https://www.youtube.com/watch?v=O4irXQhgMqg", "https://www.youtube.com/watch?v=1vrEljMfXYo",
         "https://www.youtube.com/watch?v=8AHCfZTRGiI", "https://www.youtube.com/watch?v=YkADj0TPrJA",
         "https://www.youtube.com/watch?v=S9ZbuIRPwFg", "https://www.youtube.com/watch?v=hvKyBcCDOB4"]
file = open('predictions.csv', 'w+')
for song in songs:
    res = subprocess.run(["python3", "audio-classifier.py", "-y", song, "5"], capture_output=True, text=True)
    res_str = str(res.stderr)
    print(res_str)
    file.write(res_str + '\n')

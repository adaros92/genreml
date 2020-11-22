from flask import Flask

app = Flask(__name__)

app.config["FILE_UPLOAD_LOCATION"] = "/home/ubuntu/files"
app.config["ALLOWED_EXTENSIONS"] = {'mp3', 'wav'}

from frontend import views

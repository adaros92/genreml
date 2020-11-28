import os
import sys

from genreml.model.utils.file_handling import get_filetype, get_filename
from flask import request, render_template
from werkzeug.utils import secure_filename

from frontend import app
from frontend.processing import feature_extraction, genre_prediction, downloader


def populate_visual_features(root_path, filepath):
    features, visual_features = feature_extraction.process_audio_file(root_path, filepath)
    visual_feature_relative_paths = ["/static/{0}".format(get_filename(feature)) for feature in visual_features]
    visual_feature_relative_paths = [tuple(visual_feature_relative_paths[i:i + 2])
                                     for i in range(0, len(visual_feature_relative_paths), 2)]
    os.remove(filepath)
    return visual_feature_relative_paths


@app.route('/upload', methods=['POST'])
def upload_file():
    """ Route for uploading audio files to the site """
    if request.method == 'POST':
        # Get the file information from the upload
        f = request.files['file']
        filename = secure_filename(f.filename)
        extension = get_filetype(filename).replace(".", "")
        # Process the file only if extension is allowed
        if extension in app.config['ALLOWED_EXTENSIONS']:
            filepath = os.path.join(app.config['FILE_UPLOAD_LOCATION'], filename)
            f.save(filepath)
            visual_feature_relative_paths = populate_visual_features(app.root_path, filepath)
            return render_template('results.html', visual_features=visual_feature_relative_paths)
        return render_template('index.html')


@app.route('/download_youtube', methods=['POST'])
def process_youtube_video():
    """ Route for downloading a Youtube video and performing feature extraction + prediction """
    if request.method == 'POST':
        # Get the Youtube link from the request
        youtube_url = request.form['text']
        # Only process results if valid youtube video link
        if "youtube" in youtube_url and youtube_url[:8] == "https://" and "v=" in youtube_url:
            filepath = downloader.download_link(youtube_url, directory_path=app.config['FILE_UPLOAD_LOCATION'])
            visual_feature_relative_paths = populate_visual_features(app.root_path, filepath)
            return render_template('results.html', visual_features=visual_feature_relative_paths)
    return render_template('index.html')


@app.route('/')
def index():
    """ Server route for the app's landing page """
    return render_template('index.html')


if __name__ == "__main__":
    environment = "production"
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    if environment == "production":
        from gevent.pywsgi import WSGIServer
        app.debug = True
        http_server = WSGIServer(('', 8000), app)
        http_server.serve_forever()
    elif environment == "development":
        app.run(debug=True, host='127.0.0.1', port=8000)

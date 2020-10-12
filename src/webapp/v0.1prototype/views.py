from webapp import app

from flask import Flask, url_for, request, render_template


@app.route('/classify_audio_clip', methods=['GET', 'POST'])
def classify_audio_clip():
    """ Server route to accept audio clips from users and run the Genre prediction workflow """
    if request.method == 'POST':
        # Step 1. Accept file
        # f = request.files['some_clip']
        # f.save('/var/www/uploads/some_clip.wav')
        # Step 2. Call audio processor to extract features
        # Step 3. Call spectrogram generator to generate image from audio
        # Step 4. Call prediction runner to classify the spectrograph as belonging to a certain genre
        return "This will be awesome someday"
    else:
        return "What do I do with a GET request?"


@app.route('/')
def index():
    """ Server route for the app's landing page """
    return render_template('index.html')

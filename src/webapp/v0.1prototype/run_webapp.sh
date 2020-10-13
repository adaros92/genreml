export FLASK_APP=webapp
export FLASK_ENV=production 

pip3 install -e .
python3 -m flask run

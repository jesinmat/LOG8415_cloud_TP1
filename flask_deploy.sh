#!/bin/bash

sudo apt update
sudo apt install -y python3-pip python3-venv
mkdir flask_application && cd flask_application
python3 -m venv venv

# Use the following commands to bind to port 80 without running Flask as sudo
sudo apt install authbind
sudo touch /etc/authbind/byport/80
sudo chmod 777 /etc/authbind/byport/80
#

source venv/bin/activate
pip3 install flask

INSTANCEID=`ec2metadata --instance-id`

cat <<EOF > /home/ubuntu/app.py
from flask import Flask
app = Flask(__name__)

@app.route('/cluster%s')
def my_app():
    return 'Flask application $INSTANCEID'

EOF

export FLASK_APP=/home/ubuntu/app.py
authbind --deep flask run --host 0.0.0.0 --port 80
# flask run --host 0.0.0.0

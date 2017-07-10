from flask import Flask
from flask import request
import os
import requests
app = Flask(__name__)


@app.route("/")
def hello():
    msg_id = request.args.get('id', '')
    print('Received from ' + request.remote_addr + ' msg_id:' + str(msg_id), flush=True)
    receiver = os.environ['RECEIVER']
    try:
        print('Sending request to ' + receiver + ' with msg_id:' + msg_id, flush=True)
        r = requests.get("http://" + receiver, params={'msg_id': msg_id})
        if r.status_code == 200:
            return "Ok from " + receiver + " with text:" + r.text
        else:
            return "Error from " + receiver + " with status code:" + str(r.status_code)
    except Exception as e:
        msg = "Error sending to " + receiver + " with type:" + e.__class__.__name__ + " message:" + str(e)
        print(msg, flush=True)
        return msg

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

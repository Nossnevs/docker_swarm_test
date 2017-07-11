from flask import Flask
from flask import request
app = Flask(__name__)


@app.route("/")
def hello():
    msg_id = request.args.get('msg_id', '')
    print('Received from ' + request.remote_addr + ' msg_id:' + str(msg_id), flush=True)
    return "id:" + str(msg_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

import requests
import time
import os


def requester():
    msg_id = 0
    while True:
        time.sleep(2)
        msg_id += 1
        receiver = os.environ['RECEIVER']
        r = None
        try:
            print('Sending request to ' + receiver + ' with msg_id:' + str(msg_id), flush=True)
            r = requests.get("http://" + receiver, params={'msg_id': msg_id})
        except Exception as e:
            msg = "Error sending to " + receiver + " with type:" + e.__class__.__name__ + " message:" + str(e)
            print(msg, flush=True)
            continue
        if r.status_code == 200:
            print("Ok from " + receiver + " with text:" + r.text, flush=True)
        else:
            print("Error from " + receiver + " with status code:" + str(r.status_code), flush=True)


if __name__ == '__main__':
    requester()

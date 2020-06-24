import sys
import http.client
import json

def main(path='/', data=''):

    headers = {
        'Content-type': "application/json"
    }

    data = {
        'PERSIST': True,
        'DATA': data
    }

    conn = http.client.HTTPConnection("127.0.0.1:5001")
    conn.request("POST", path, json.dumps(data).encode(), headers)
    connect_hangr_response = conn.getresponse()

    print(connect_hangr_response.status, connect_hangr_response.reason, connect_hangr_response.read())

if __name__ == "__main__":

    try:
        path=sys.argv[1]
    except:
        path='/'

    try:
        data=sys.argv[2]
    except:
        data=''

    print(path)

    main(path=path, data=data)

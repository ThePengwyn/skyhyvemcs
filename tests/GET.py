import sys
import http.client
import json

def main(path='/'):

    headers = {
        'Content-type': "application/json"
    }

    data = {

    }

    conn = http.client.HTTPConnection("127.0.0.1:5001")
    conn.request("GET", path, json.dumps(data).encode(), headers)
    connect_hangr_response = conn.getresponse()

    print(connect_hangr_response.status, connect_hangr_response.reason, connect_hangr_response.read())

if __name__ == "__main__":

    try:
        path=sys.argv[1]
    except:
        path='/'

    print(path)

    main(path=path)

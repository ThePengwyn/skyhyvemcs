import http.client
import json

headers = {
    'Content-type': "application/json"
}

data = {

}

conn = http.client.HTTPConnection("127.0.0.1:5001")
conn.request("GET", "/", json.dumps(data).encode(), headers)
connect_hangr_response = conn.getresponse()

print(connect_hangr_response.status, connect_hangr_response.reason, connect_hangr_response.read())

#!/usr/bin/python3
import requests
import time
from requests.auth import HTTPBasicAuth

# change these values
google_maps_api_endpoint = "https://maps.googleapis.com/maps/api/directions/json?"
google_maps_api_key = "xxxxxxxxxxxx"
domoticz_enpoint = "http://127.0.0.1:8080/json.htm?"
domoticz_basicauth_username = 'username'
domoticz_basicauth_password = 'password'
domoticz_sensors = [
  {
    'idx': 11,
    'origin': '22.4507663,114.0259901',
    'destination': '22.4528694,114.1799718',
  },
  {
    'idx': 10,
    'destination': '22.4507663,114.0259901',
    'origin': '22.4528694,114.1799718',
  },
]
# End

auth = HTTPBasicAuth(domoticz_basicauth_username, domoticz_basicauth_password)
for sensor in domoticz_sensors:
  google_maps_api_query = {
    'origin': sensor['origin'],
    'destination': sensor['destination'],
    'key': google_maps_api_key,
    'departure_time': int(time.mktime(time.localtime()))
  }
  response = requests.get(google_maps_api_endpoint,  params=google_maps_api_query)
  if response.status_code == 200:
    data = response.json()
    if data['status'] == 'OK':
      duration = data['routes'][0]['legs'][0]['duration_in_traffic']
      summary = data['routes'][0]['summary']
      alert_level = 0
      if duration['value'] <= 1800:
        alert_level = 1
      if duration['value'] > 1800 and duration['value'] <= 2400:
        alert_level = 2
      if duration['value'] > 2400 and duration['value'] <= 3000:
        alert_level = 3
      if duration['value'] > 3000:
        alert_level = 4

      domoticz_udevice_query = {
        'type': 'command',
        'param': 'udevice',
        'idx': sensor['idx'],
        'nvalue': alert_level,
        'svalue':  duration['text'] + ' via ' + summary
      }
      requests.get(domoticz_enpoint, params=domoticz_udevice_query, auth=auth)



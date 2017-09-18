#!/usr/bin/python3
from libpurecoollink.dyson import DysonAccount

from libpurecoollink.dyson_pure_state import DysonPureHotCoolState, \
  DysonPureCoolState, DysonEnvironmentalSensorState

import requests

dyson_account_email = 'account@email.com'
dyson_account_password = 'password'
country = 'HK'

domoticz_enpoint = "http://127.0.0.1:8080/json.htm?"
domoticz_sensors = [
  {
    'name': 'air_quality',
    'idx': 21
  },
  {
    'name': 'temperature_humidity',
    'idx': 19
  },
  {
    'name': 'dust',
    'idx': 20
  },
]

domoticz_udevice_query = {
  'type': 'command',
  'param': 'udevice',
  'idx': 0,
  'nvalue': 0,
  'svalue': ''
}

# Log to Dyson account
# Language is a two characters code (eg: FR)
dyson_account = DysonAccount(dyson_account_email, dyson_account_password, country)
logged = dyson_account.login()

if not logged:
    print('Unable to login to Dyson account')
    exit(1)

# List devices available on the Dyson account
devices = dyson_account.devices()

# for now i just have one Dyson device
device = devices[0]
connected = device.auto_connect()
if connected:
  try:

    for sensor in domoticz_sensors:
      domoticz_udevice_query['idx'] = sensor['idx']

      if sensor['name'] == 'dust':
        domoticz_udevice_query['svalue'] = device.environmental_state.dust

      if sensor['name'] == 'air_quality':
        domoticz_udevice_query['svalue'] = device.environmental_state.volatil_organic_compounds

      if sensor['name'] == 'temperature_humidity':
        hum_stat = 0
        if device.environmental_state.humidity < 30:
          hum_stat = 2
        if device.environmental_state.humidity >= 30 and device.environmental_state.humidity < 45:
          hum_stat = 0
        if device.environmental_state.humidity >= 45 and device.environmental_state.humidity <= 75:
          hum_stat = 1
        if device.environmental_state.humidity > 75:
          hum_stat = 3
        domoticz_udevice_query['svalue'] = ";".join(['{:.2}'.format(device.environmental_state.temperature / 10), str(device.environmental_state.humidity), str(hum_stat)])

      requests.get(domoticz_enpoint, params=domoticz_udevice_query)
  finally:
    device.disconnect()
    pass


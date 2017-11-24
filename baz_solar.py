#!/usr/bin/python3

import requests
import json
from astral import *  # http://pythonhosted.org/astral/
# import sys
from math import sin, radians
import time
# import os
# import smtplib
from datetime import date, timedelta, datetime
from matplotlib import pyplot as plt
import pickle
# from datetime import timedelta, datetime
# from email.mime.text import MIMEText

COUNTRY = "Ireland"
CITY = "Wexford"
wgKEY = pickle.load(open("wunderground.key.pkl", "rb"))  # wunderground key (500 calls/day, 10 calls/min)
freshness = 'pickled'
# freshness = 'fresh'

# Mapping of conditions to a level of cloud cover.  These can be adjusted
# since they are all made up anyway
conditions = {
    "Blowing Snow": 8,
    "Clear": 0,
    "Fog": 5,
    "Haze": 2,
    "Heavy Blowing Snow": 9,
    "Heavy Fog": 9,
    "Heavy Low Drifting Snow": 10,
    "Heavy Rain": 10,
    "Heavy Rain Showers": 10,
    "Heavy Thunderstorms and Rain": 10,
    "Light Drizzle": 10,
    "Drizzle": 10,
    "Heavy Drizzle": 10,
    "Light Freezing Rain": 10,
    "Light Ice Pellets": 10,
    "Light Rain": 10,
    "Light Rain Showers": 10,
    "Light Snow": 10,
    "Light Snow Grains": 10,
    "Light Snow Showers": 10,
    "Light Thunderstorms and Rain": 10,
    "Low Drifting Snow": 10,
    "Mist": 3,
    "Mostly Cloudy": 8,
    "Overcast": 10,
    "Partial Fog": 2,
    "Partly Cloudy": 5,
    "Patches of Fog": 2,
    "Rain": 10,
    "Rain Showers": 10,
    "Scattered Clouds": 4,
    "Shallow Fog": 3,
    "Snow": 10,
    "Snow Showers": 10,
    "Thunderstorm": 10,
    "Thunderstorms and Rain": 10,
    "Unknown": 5
}

num_days = 30
today = date.today()
start_date = today - timedelta(num_days)
# today = datetime(2016, 12, 25)

timeplot = list()
insoplot = list()
clearplot = list()

maxrate = 10  # queries per minute

a = Astral()
location = a["Dublin"]

# pickled
if freshness is 'pickled':
    datadict = pickle.load(open("datadict.pkl", "rb"))
    dates = sorted(datadict.keys())

    for datestring in dates[29:30]:
        querydate = datetime.strptime(datestring, "%Y%m%d")
        sun = location.sun(local=True, date=querydate)
        data = datadict[str(datestring)]
        print(datestring)

        for d in data:
            year = int(d['date']['year'])
            month = int(d['date']['mon'])
            day = int(d['date']['mday'])
            hour = int(d['date']['hour'])
            minute = int(d['date']['min'])
            dawn = sun['dawn']
            dusk = sun['dusk']
            dateandtime = datetime(year, month, day, hour, minute)
            elevation_now = a.solar_elevation(dateandtime=dateandtime, latitude=location.latitude, longitude=location.longitude)
            elevation_old = a.solar_elevation(dateandtime=dateandtime - timedelta(1 / 24), latitude=location.latitude, longitude=location.longitude)

            hourmin = hour * 60 + minute
            dawntime = int(dawn.hour) * 60 + int(dawn.minute)
            dusktime = int(dusk.hour) * 60 + int(dusk.minute)

            cloud_cover = conditions[d['conds']] / 10
            clear_sky_insolation = 990 * sin(radians((elevation_now + elevation_old) / 2))
            current_insolation = clear_sky_insolation * (1 - 0.75 * cloud_cover**(3.4))
            if hourmin >= dawntime and hourmin <= dusktime:
                timeplot.append(dateandtime)
                insoplot.append(current_insolation)
                clearplot.append(clear_sky_insolation)
# !pickled

# fresh
if freshness is 'fresh':
    datadict = dict()
    for day in range(num_days):
        time.sleep(60 / maxrate + 1)  # wait 7 seconds between queries to not overload wunderground
        querydate = start_date + timedelta(day)
        datestring = querydate.strftime("%Y%m%d")

        # get dawn, dusk & sunset times
        sun = location.sun(local=True, date=querydate)
        # In : sun.keys()
        # Out: dict_keys(['dawn', 'sunrise', 'noon', 'sunset', 'dusk'])
        print(datestring)

        historyURL = 'http://api.wunderground.com/api/' + wgKEY + '/history_' + datestring + '/q/' + COUNTRY + '/' + CITY + '.json'

        r = requests.get(historyURL)
        if r.status_code != 200:
            exit()
        data = r.json()['history']['observations']
        datadict[str(datestring)] = data

        # data = json.load(open('Dublin.json', 'r'))['history']['observations']

        for d in data:
            year = int(d['date']['year'])
            month = int(d['date']['mon'])
            day = int(d['date']['mday'])
            hour = int(d['date']['hour'])
            minute = int(d['date']['min'])
            dawn = sun['dawn']
            dusk = sun['dusk']
            dateandtime = datetime(year, month, day, hour, minute)

            elevation_now = a.solar_elevation(dateandtime=dateandtime, latitude=location.latitude, longitude=location.longitude)
            elevation_old = a.solar_elevation(dateandtime=dateandtime - timedelta(1 / 24), latitude=location.latitude, longitude=location.longitude)

            hourmin = hour * 60 + minute
            dawntime = int(dawn.hour) * 60 + int(dawn.minute)
            dusktime = int(dusk.hour) * 60 + int(dusk.minute)

            cloud_cover = conditions[d['conds']] / 10
            # print(conditions[d['conds']] / 10, end='\t')
            clear_sky_insolation = 990 * sin(radians((elevation_now + elevation_old) / 2))
            current_insolation = clear_sky_insolation * (1 - 0.75 * cloud_cover**(3.4))
            if hourmin >= dawntime and hourmin <= dusktime:
                timeplot.append(dateandtime)
                insoplot.append(current_insolation)
                clearplot.append(clear_sky_insolation)
            # print(str(round(current_insolation)) + " W/m^2")

    pickle.dump(datadict, open("datadict.pkl", "wb"))
# !fresh

plt.plot(timeplot, insoplot)
plt.plot(timeplot, clearplot)
plt.ylim(0, max(clearplot))
plt.show()

#!/usr/bin/python3

import requests
# import json
from astral import *  # http://pythonhosted.org/astral/
# import sys
from math import sin, radians
# import time
# import os
# import smtplib
from datetime import timedelta, datetime
import pytz
from matplotlib import pyplot as plt
import pickle
# from datetime import timedelta, datetime
# from email.mime.text import MIMEText

COUNTRY = "Ireland"
CITY = "Wexford"
wgKEY = pickle.load(open("wunderground.key.pkl", "rb"))  # wunderground key (500 calls/day, 10 calls/min)
dsKEY = pickle.load(open("darksky.key.pkl", "rb"))  # darksky.net key (1000 calls/day) replace with your key
# freshness = 'pickled'
freshness = 'fresh'

num_days = 365
today = datetime.today()
# today = datetime(2016, 12, 25)
start_date = today - timedelta(num_days)

thermal_coeff = 0.0045  # efficiency change (+/-) per 1*C away from 25*C
baseline_eff = 0.12  # electrical efficiency (average from https://doi.org/10.1016/j.egypro.2013.05.072)

timeplot = list()
insoplot = list()
clearplot = list()
powerplot = list()

a = Astral()
# location = a["Dublin"]
location = Location()
location.timezone = a.geocoder['Dublin'].timezone
location.elevation = a.geocoder['Dublin'].elevation
# location.name = "Smithfield Village"
# location.region = "Dublin"
# location.latitude = 53.348426
# location.longitude = -6.276576

# location.name = "Good Shepherd Convent"
# location.region = "Limerick"
# location.latitude = 52.652021
# location.longitude = -8.615550

location.name = "St Petersburg"
location.region = "FL"
location.latitude = 27.7909323
location.longitude = -82.6319695

# fresh
if freshness is 'fresh':
    try:
        datadict = dict()
        for day in range(num_days):
            querydate = start_date + timedelta(day)
            datestring = querydate.strftime("%Y%m%d")

            # get dawn, dusk & sunset times
            sun = location.sun(local=True, date=querydate)

            print(datestring)
            historyURL = 'https://api.darksky.net/forecast/' + dsKEY + '/' + str(location.latitude) + ',' + str(location.longitude) + ',' + str(round(querydate.timestamp())) + '?exclude=currently&units=ca'
            # time in format '%Y-%m-%dT%k:%M:%S%z' or '%s'

            r = requests.get(historyURL)
            if r.status_code != 200:
                print(r.json())
                exit()
            if int(r.headers['X-Forecast-API-Calls']) > 900:
                print("WARNING Nearing Daily API Limit")
                print(r.headers['X-Forecast-API-Calls'] + ' calls made so far today (of 1000 max)')
            if int(r.headers['X-Forecast-API-Calls']) > 995:
                print("Maximum number of calls reached for today, try again tomorrow")
                exit()
            data = r.json()['hourly']['data']
            datadict[str(datestring)] = data

            # data = json.load(open('Dublin.json', 'r'))['history']['observations']

            for d in data:
                dateandtime = datetime.fromtimestamp(d['time'])
                dateandtime = pytz.timezone(location.timezone).localize(dateandtime)  # apparently this is the prefered method for Astral
                dawn = sun['dawn']
                dusk = sun['dusk']

                try:
                    temperature = d['temperature']
                except KeyError:
                    continue

                tempDiff = 25 - temperature
                effDiff = tempDiff * thermal_coeff
                efficiency = baseline_eff - effDiff

                elevation_now = a.solar_elevation(dateandtime=dateandtime, latitude=location.latitude, longitude=location.longitude)
                elevation_old = a.solar_elevation(dateandtime=dateandtime - timedelta(1 / 24), latitude=location.latitude, longitude=location.longitude)

                # hourmin = hour * 60 + minute
                # dawntime = int(dawn.hour) * 60 + int(dawn.minute)
                # dusktime = int(dusk.hour) * 60 + int(dusk.minute)

                try:
                    cloud_cover = d['cloudCover']
                    print(d['cloudCover'], end='\t')
                except KeyError:
                    continue

                try:
                    print(d['summary'])
                except KeyError:
                    pass
                clear_sky_insolation = 990 * sin(radians((elevation_now + elevation_old) / 2))  # from http://www.shodor.org/os411/courses/_master/tools/calculators/solarrad/
                current_insolation = clear_sky_insolation * (1 - 0.75 * cloud_cover**(3.4))
                power = efficiency * current_insolation
                if dateandtime >= dawn and dateandtime <= dusk:
                    timeplot.append(dateandtime)
                    insoplot.append(current_insolation)
                    clearplot.append(clear_sky_insolation)
                    powerplot.append(power)
                # print(str(round(current_insolation)) + " W/m^2")
    except:
        pickle.dump(datadict, open("ds_datadict_st_pete.pkl", "wb"))
        print('some error happened')
        exit()
    pickle.dump(datadict, open("ds_datadict_st_pete.pkl", "wb"))
# !fresh

# pickled
if freshness is 'pickled':
    datadict = pickle.load(open("ds_datadict.pkl", "rb"))
    dates = sorted(datadict.keys())

    for datestring in dates:
        querydate = datetime.strptime(datestring, "%Y%m%d")
        sun = location.sun(local=True, date=querydate)
        data = datadict[str(datestring)]

        for d in data:
            dateandtime = datetime.fromtimestamp(d['time'])
            dateandtime = pytz.timezone(location.timezone).localize(dateandtime)  # apparently this is the prefered method for Astral
            dawn = sun['dawn']
            dusk = sun['dusk']
            elevation_now = a.solar_elevation(dateandtime=dateandtime, latitude=location.latitude, longitude=location.longitude)
            elevation_old = a.solar_elevation(dateandtime=dateandtime - timedelta(1 / 24), latitude=location.latitude, longitude=location.longitude)

            cloud_cover = d['cloudCover']
            clear_sky_insolation = 990 * sin(radians((elevation_now + elevation_old) / 2))
            current_insolation = clear_sky_insolation * (1 - 0.75 * cloud_cover**(3.4))
            if dateandtime >= dawn and dateandtime <= dusk:
                pass
            timeplot.append(dateandtime)
            insoplot.append(current_insolation)
            clearplot.append(clear_sky_insolation)
# !pickled

plt.plot(timeplot, insoplot)
plt.plot(timeplot, clearplot)
plt.plot(timeplot, powerplot)
plt.ylim(0, max(clearplot))
plt.savefig('12months_st_pete.png', bbox_inches='tight')

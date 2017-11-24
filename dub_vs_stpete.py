import pickle
from matplotlib import pyplot as plt
from astral import *  # http://pythonhosted.org/astral/

from math import sin, radians

from datetime import timedelta, datetime

import pytz

dublin_datadict = pickle.load(open("ds_datadict.pkl", "rb"))
stpete_datadict = pickle.load(open("ds_datadict_st_pete.pkl", "rb"))
a = Astral()

thermal_coeff = 0.0045  # efficiency change (+/-) per 1*C away from 25*C
baseline_eff = 0.12  # electrical efficiency (average from https://doi.org/10.1016/j.egypro.2013.05.072)

location = Location()
location.timezone = a.geocoder['Dublin'].timezone
location.elevation = a.geocoder['Dublin'].elevation
# location.name = "Smithfield Village"
# location.region = "Dublin"
# location.latitude = 53.348426
# location.longitude = -6.276576

dates = sorted(stpete_datadict.keys())
timeplot = list()
insoplot = list()
clearplot = list()
powerplot = list()

location.name = "St Petersburg"
location.region = "FL"
location.latitude = 27.7909323
location.longitude = -82.6319695

for datestring in dates:
    querydate = datetime.strptime(datestring, "%Y%m%d")
    sun = location.sun(local=True, date=querydate)
    data = stpete_datadict[str(datestring)]
    powers = list()

    for d in data:
        dateandtime = datetime.fromtimestamp(d['time'])
        dateandtime = pytz.timezone(location.timezone).localize(dateandtime)  # apparently this is the prefered method for Astral
        dawn = sun['dawn']
        dusk = sun['dusk']
        elevation_now = a.solar_elevation(dateandtime=dateandtime, latitude=location.latitude, longitude=location.longitude)
        elevation_old = a.solar_elevation(dateandtime=dateandtime - timedelta(1 / 24), latitude=location.latitude, longitude=location.longitude)
        try:
            temperature = d['temperature']
        except KeyError:
            continue

        tempDiff = 25 - temperature
        effDiff = tempDiff * thermal_coeff
        efficiency = baseline_eff - effDiff

        try:
            cloud_cover = d['cloudCover']
        except KeyError:
            continue
        clear_sky_insolation = 990 * sin(radians((elevation_now + elevation_old) / 2))
        current_insolation = clear_sky_insolation * (1 - 0.75 * cloud_cover**(3.4))
        power = efficiency * current_insolation

        if dateandtime >= dawn and dateandtime <= dusk:
            pass
        insoplot.append(current_insolation)
        clearplot.append(clear_sky_insolation)
        powers.append(power)
    timeplot.append(querydate)
    powerplot.append(max(powers))

plt.plot(timeplot, powerplot, label="St Petersburg, FL")
plt.ylim(0, max(powerplot))

location.name = "Good Shepherd Convent"
location.region = "Limerick"
location.latitude = 52.652021
location.longitude = -8.615550


dates = sorted(dublin_datadict.keys())
timeplot = list()
insoplot = list()
clearplot = list()
powerplot = list()

for datestring in dates:
    querydate = datetime.strptime(datestring, "%Y%m%d")
    sun = location.sun(local=True, date=querydate)
    data = dublin_datadict[str(datestring)]
    powers = list()

    for d in data:
        dateandtime = datetime.fromtimestamp(d['time'])
        dateandtime = pytz.timezone(location.timezone).localize(dateandtime)  # apparently this is the prefered method for Astral
        dawn = sun['dawn']
        dusk = sun['dusk']
        elevation_now = a.solar_elevation(dateandtime=dateandtime, latitude=location.latitude, longitude=location.longitude)
        elevation_old = a.solar_elevation(dateandtime=dateandtime - timedelta(1 / 24), latitude=location.latitude, longitude=location.longitude)
        try:
            temperature = d['temperature']
        except KeyError:
            continue

        tempDiff = 25 - temperature
        effDiff = tempDiff * thermal_coeff
        efficiency = baseline_eff - effDiff

        try:
            cloud_cover = d['cloudCover']
        except KeyError:
            continue
        clear_sky_insolation = 990 * sin(radians((elevation_now + elevation_old) / 2))
        current_insolation = clear_sky_insolation * (1 - 0.75 * cloud_cover**(3.4))
        power = efficiency * current_insolation

        if dateandtime >= dawn and dateandtime <= dusk:
            pass
        insoplot.append(current_insolation)
        clearplot.append(clear_sky_insolation)
        powers.append(power)
    timeplot.append(querydate)
    powerplot.append(max(powers))

plt.plot(timeplot, powerplot, label="Good Shepherd Convent, Limerick")
plt.ylabel("Power (W/m^2)")
plt.legend()
plt.title("Maximum Solar Panel Power Output")

# plt.savefig('12months_st_pete_dublin.png', bbox_inches='tight')
plt.show()

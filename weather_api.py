import requests


BASE_URL = 'http://api.openweathermap.org/data/2.5{}'
ICON_URI = 'http://openweathermap.org/img/wn/{}@2x.png'
PARAMS = dict(
    appid='925347ab594e70ec4ab7ad0c0efe4d3f',
    units='metric',
    exclude='minutely,alerts',
)


def get_current(lat, lon):
    params = PARAMS.copy()
    params['lat'], params['lon'] = lat, lon

    response = requests.get(BASE_URL.format('/onecall'), params=params).json()
    part = response['current']
    part['timezone'] = response['timezone']

    return part


def get_hours(hours, lat, lon):
    params = PARAMS.copy()
    params['lat'], params['lon'] = lat, lon

    response = requests.get(BASE_URL.format('/onecall'), params=params).json()
    try:
        part = response['hourly'][int(hours)]
    except IndexError:
        return
    part['timezone'] = response['timezone']

    return part


def get_days(days, lat, lon):
    params = PARAMS.copy()
    params['lat'], params['lon'] = lat, lon

    response = requests.get(BASE_URL.format('/onecall'), params=params).json()
    try:
        part = response['daily'][int(days)]
    except IndexError:
        return
    part['timezone'] = response['timezone']

    return part


def get_coords(city):
    params = PARAMS.copy()
    params['q'] = city

    response = requests.get(BASE_URL.format('/weather'), params=params).json()

    if response['cod'] == '404':
        return
    else:
        return [response['coord']['lat'], response['coord']['lon']]


def parse_icon(icon_id):
    return ICON_URI.format(icon_id)

# Python Nightscout client

[![PyPi](https://img.shields.io/pypi/v/py_nightscout)](https://pypi.org/project/py-nightscout/)

A simple async python client for accessing data stored in [Nightscout](https://github.com/nightscout/cgm-remote-monitor)
Based on [ps2/python-nightscout](https://github.com/ps2/python-nightscout)

## Example Usage

```python
import asyncio
import datetime

from aiohttp import ClientError, ClientConnectorError, ClientResponseError

import py_nightscout as nightscout

import pytz

NIGHTSCOUT_URL = 'https://yournightscoutsite.herokuapp.com'
API_SECRET = ''

async def main():
    """Example of library usage."""
    try:
        if api_secret:
                # To use authentication, use yout api secret:
                api = nightscout.Api(NIGHTSCOUT_API, api_secret=API_SECRET)
        else:
            # You can use the api without authentication:
            api = nightscout.Api(NIGHTSCOUT_URL)
        status = await api.get_server_status()
    except ClientResponseError as error:
        raise RuntimeError("Received ClientResponseError") from error
    except (ClientError, ClientConnectorError, TimeoutError, OSError) as error:
        raise RuntimeError("Received client error or timeout") from error


    #### Glucose Values (SGVs) ####
    # Get last 10 entries:
    entries = await api.get_sgvs()
    print([entry.sgv for entry in entries])

    # Specify time ranges:
    entries = await api.get_sgvs({'count':0, 'find[dateString][$gte]': '2017-03-07T01:10:26.000Z'})
    print([entry.sgv for entry in entries])

    ### Treatments ####
    # To fetch recent treatments (boluses, temp basals):
    treatments = await api.get_treatments()
    print([treatment.eventType for treatment in treatments])

    ### Profiles
    profile_definition_set = await api.get_profiles()
    profile_definition = profile_definition_set.get_profile_definition_active_at(datetime.datetime.now(tz=pytz.UTC))
    profile = profile_definition.get_default_profile()

    print("Duration of insulin action = %d" % profile.dia)

    five_thirty_pm = datetime.datetime(2017, 3, 24, 17, 30)
    five_thirty_pm = profile.timezone.localize(five_thirty_pm)
    print("Scheduled basal rate at 5:30pm is = %f" % profile.basal.value_at_date(five_thirty_pm))

    ### Server Status

    server_status = await api.get_server_status()
    print(server_status.status)
    
asyncio.run(main())
```

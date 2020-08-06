# Python Nightscout client

[![PyPi](https://img.shields.io/pypi/v/py_nightscout)](https://pypi.org/project/py-nightscout/)

A simple async python client for accessing data stored in [Nightscout](https://github.com/nightscout/cgm-remote-monitor)
Based on [ps2/python-nightscout](https://github.com/ps2/python-nightscout)

## Example Usage

```python
import asyncio

from aiohttp import ClientResponseError, ClientConnectorError

import py_nightscout as nightscout

async def main():
    """Example of library usage."""

    # You can use the api without authentication:
    api = nightscout.Api('https://yournightscoutsite.herokuapp.com')
    # To use authentication, use yout api secret:
    api = nightscout.Api('https://yournightscoutsite.herokuapp.com', api_secret='your api secret')

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
    profile_definition_set = api.get_profiles()
    profile_definition = profile_definition_set.get_profile_definition_active_at(datetime.now())
    profile = profile_definition.get_default_profile()

    print "Duration of insulin action = %d" % profile.dia

    five_thirty_pm = datetime(2017, 3, 24, 17, 30)
    five_thirty_pm = profile.timezone.localize(five_thirty_pm)
    print "Scheduled basal rate at 5:30pm is = %f" % profile.basal.value_at_date(five_thirty_pm)

    ### Server Status

    server_status = api.get_status()
    print(server_status.status)
```

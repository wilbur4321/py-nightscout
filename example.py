import asyncio
import datetime
import platform
import pytz
import argparse

from aiohttp import ClientError, ClientConnectorError, ClientResponseError

import py_nightscout as nightscout

async def main():
    """Example of library usage."""
    parser = argparse.ArgumentParser(description="Example of py-nightscout library")
    parser.add_argument("url", help="Nightscout URL")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-s", "--api-secret", help="API secret (deprecated)", required=False)
    group.add_argument("-t", "--access-token", help="Access token", required=False)
    args = parser.parse_args()

    try:
        api = nightscout.Api(
            args.url,
            access_token=args.access_token,
            api_secret=args.api_secret,
        )
    except ClientResponseError as error:
        raise RuntimeError("Received ClientResponseError") from error
    except (ClientError, ClientConnectorError, TimeoutError, OSError) as error:
        raise RuntimeError("Received client error or timeout") from error


    #### Glucose Values (SGVs) ####
    # Get last 10 entries:
    entries = await api.get_sgvs()
    print("SGV values in mg/dL:")
    print([entry.sgv for entry in entries])
    print("SGV values in mmol/L:")
    print([entry.sgv_mmol for entry in entries])

    # Specify time ranges:
    entries = await api.get_sgvs({'count':0, 'find[dateString][$lte]': '2017-03-07T01:10:26.000Z'})
    print("\nSGV values on timerange:")
    print([entry.sgv for entry in entries])

    ### Treatments ####
    # To fetch recent treatments (boluses, temp basals):
    treatments = await api.get_treatments()
    print("\nTreatments:")
    print([treatment.eventType for treatment in treatments])

    ### Profiles
    profile_definition_set = await api.get_profiles()
    profile_definition = profile_definition_set.get_profile_definition_active_at(datetime.datetime.now(tz=pytz.UTC))
    profile = profile_definition.get_default_profile()

    print("\nDuration of insulin action = %d" % profile.dia)

    five_thirty_pm = datetime.datetime(2017, 3, 24, 17, 30)
    five_thirty_pm = profile.timezone.localize(five_thirty_pm)
    print("\nScheduled basal rate at 5:30pm is = %f" % profile.basal.value_at_date(five_thirty_pm))

    ### Server Status

    server_status = await api.get_server_status()
    print("\nserver status: %s" % server_status.status)

    ### Device Status

    print("\nDevices:")
    devices_status = await api.get_latest_devices_status()
    for device_key in devices_status:
         print("\t%s battery: %d%%" % (device_key, devices_status[device_key].uploader.battery))
    
if platform.system()=='Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(main())
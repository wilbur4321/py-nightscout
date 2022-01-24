"""A library that provides a Python interface to Nightscout"""
import hashlib
from typing import Any, Callable, Dict, List, Optional

from aiohttp import ClientSession, ClientTimeout
from .models import SGV, ProfileDefinitionSet, ServerStatus, Treatment, DeviceStatus


ParamsDict = Optional[Dict[str,Any]]

class Api(object):
    """A python interface into Nightscout

    Example usage:
      To create an instance of the nightscout.Api class, with no authentication:
        >>> import nightscout
        >>> api = nightscout.Api('https://yournightscoutsite.herokuapp.com')
      To use authentication, instantiate the nightscout.Api class with your
      api secret:
        >>> api = nightscout.Api('https://yournightscoutsite.herokuapp.com', api_secret='your api secret')
      To fetch recent sensor glucose values (SGVs):
        >>> entries = api.get_sgvs()
        >>> print([entry.sgv for entry in entries])
    """

    def __init__(
        self,
        server_url: str,
        *,
        access_token: Optional[str] = None,
        api_secret: Optional[str] = None,
        session: Optional[ClientSession] = None,
        timeout: Optional[ClientTimeout] = None,
    ):
        """Instantiate a new Api object."""
        self.server_url = server_url.strip("/")
        self._api_kwargs = {"headers": self.request_headers(access_token, api_secret)}
        if timeout:
            self._api_kwargs["timeout"] = timeout
        self._session = session

    def request_headers(self, access_token: Optional[str] = None, api_secret: Optional[str] = None):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if access_token:
            headers["api-secret"] = "token=" + access_token
        elif api_secret:
            if api_secret.startswith("token="):
                headers["api-secret"] = api_secret
            else:
                headers["api-secret"] = hashlib.sha1(api_secret.encode("utf-8")).hexdigest()
        return headers

    async def get_sgvs(self, params: ParamsDict = None) -> List[SGV]:
        """Fetch sensor glucose values
        Args:
          params:
            Mongodb style query params. For example, you can do things like:
                get_sgvs({'count':0, 'find[dateString][$gte]': '2017-03-07T01:10:26.000Z'})
        Returns:
          A list of SGV objects
        """
        json = await self.__get("/api/v1/entries/sgv.json", params)

        return [SGV.new_from_json_dict(x) for x in json]

    async def get_server_status(self, params: ParamsDict = None) -> ServerStatus:
        """Fetch server status
        Returns:
          The current server status
        """
        json = await self.__get("/api/v1/status.json", params)

        return ServerStatus.new_from_json_dict(json)

    async def get_treatments(self, params: ParamsDict = None) -> List[Treatment]:
        """Fetch treatments
        Args:
          params:
            Mongodb style query params. For example, you can do things like:
                get_treatments({'count':0, 'find[timestamp][$gte]': '2017-03-07T01:10:26.000Z'})
        Returns:
          A list of Treatments
        """

        json = await self.__get("/api/v1/treatments.json", params)

        return [Treatment.new_from_json_dict(x) for x in json]

    async def get_profiles(self, params: ParamsDict = None) -> List[ProfileDefinitionSet]:
        """Fetch profiles
        Args:
          params:
            Mongodb style query params. For example, you can do things like:
                get_profiles({'count':0, 'find[startDate][$gte]': '2017-03-07T01:10:26.000Z'})
        Returns:
          ProfileDefinitionSet
        """
        json = await self.__get("/api/v1/profile.json", params)
        return ProfileDefinitionSet.new_from_json_array(json)

    async def get_devices_status(self, params: ParamsDict = None) -> List[DeviceStatus]:
        """Fetch devices status
        Args:
          params:
            Mongodb style query params. For example, you can do things like:
                get_profiles({'count':0, 'find[startDate][$gte]': '2017-03-07T01:10:26.000Z'})
        Returns:
          ProfileDefinitionSet
        """
        json = await self.__get("/api/v1/devicestatus.json", params)
        return [DeviceStatus.new_from_json_dict(x) for x in json]

    async def get_latest_devices_status(self, params: ParamsDict = None) -> List[DeviceStatus]:
        """Fetch devices status
        Args:
          params:
            Mongodb style query params. For example, you can do things like:
                get_profiles({'count':0, 'find[startDate][$gte]': '2017-03-07T01:10:26.000Z'})
        Returns:
          ProfileDefinitionSet
        """
        results = await self.get_devices_status(params)
        grouped = dict()
        for entry in results:
            grouped.setdefault(entry.device, []).append(entry)
        output = dict()
        for device_name in grouped:
            entries = grouped[device_name]
            entries.sort(key=lambda x: x.created_at, reverse=True)
            output[device_name] = entries[0]
        return output

    async def __get(self, path, params: ParamsDict = None):
        async def get(session: ClientSession):
            async with session.get(
                f"{self.server_url}{path}", params=params, **self._api_kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

        return await self.__call(get)

    async def __call(self, handler: Callable[[ClientSession], Any]):
        if not self._session:
            async with ClientSession() as request_session:
                return await handler(request_session)
        else:
            return await handler(self._session)

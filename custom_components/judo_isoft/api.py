import aiohttp
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class JudoAPI:
    def __init__(self, ip, username, password):
        self.base_url = f"http://{ip}/api/rest"
        self.auth = aiohttp.BasicAuth(username, password)

    async def get_data(self, endpoint):
        """Asynchroner API-Request mit aiohttp."""
        url = f"{self.base_url}/{endpoint}"
        _LOGGER.info(f"Judo API: Sende Anfrage an {url}")

        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return None
                    data = await response.json()
                    return data.get("data")
            except Exception as e:
                _LOGGER.error(f"Fehler beim API-Request: {e}")
                return None

    async def set_data(self, endpoint, value):
        """Asynchrones API-Update mit aiohttp."""
        url = f"{self.base_url}/{endpoint}"
        payload = {"data": value}
        _LOGGER.info(f"Judo API: Sende POST an {url} mit Payload {payload}")

        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error(f"API-Fehler: {response.status} - {await response.text()}")
                        return False
                    return True
            except Exception as e:
                _LOGGER.error(f"Fehler beim API-Update: {e}")
                return False

    async def get_wasserhaerte(self):
        """Ruft die Wasserhärte ab."""
        data = await self.get_data("5100")
        return int(data[:2], 16) if data else None

    async def get_salzstand(self):
        """Ruft den Salzstand ab."""
        data = await self.get_data("5600")
        return int(data[:4], 16) if data else None

    async def start_regeneration(self):
        """Startet die Regeneration."""
        return await self.set_data("350000", "")

    async def set_wasserhaerte(self, haerte):
        """Setzt die gewünschte Wasserhärte."""
        hex_value = f"{haerte:02X}"
        return await self.set_data("3000", hex_value)

    async def set_leckageschutz(self, status):
        """Schließt oder öffnet den Leckageschutz."""
        return await self.set_data("3C00" if status else "3D00", "")

    async def set_urlaubsmodus(self, status):
        """Aktiviert oder deaktiviert den Urlaubsmodus."""
        return await self.set_data("4100", "01" if status else "00")

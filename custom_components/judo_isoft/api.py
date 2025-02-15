import requests

class JudoAPI:
    def __init__(self, ip, username, password):
        self.base_url = f"http://{ip}/api/rest"
        self.auth = (username, password)  # Auth-Daten speichern

    def get_data(self, endpoint):
        """Generische Methode zum Abrufen von Daten mit Authentifizierung."""
        response = requests.get(f"{self.base_url}/{endpoint}", auth=self.auth)
        if response.status_code == 200:
            return response.json().get("data")
        return None

    def set_data(self, endpoint, value):
        """Generische Methode zum Setzen von Daten mit Authentifizierung."""
        payload = {"data": value}
        response = requests.post(f"{self.base_url}/{endpoint}", json=payload, auth=self.auth)
        return response.status_code == 200

    def get_wasserhaerte(self):
        return int(self.get_data("5100")[:2], 16)

    def get_salzstand(self):
        data = self.get_data("5600")
        return int(data[:4], 16) if data else None

    def start_regeneration(self):
        return self.set_data("350000", "")

    def set_wasserhaerte(self, haerte):
        hex_value = f"{haerte:02X}"
        return self.set_data("3000", hex_value)

    def set_leckageschutz(self, status):
        return self.set_data("3C00" if status else "3D00", "")

    def set_urlaubsmodus(self, status):
        return self.set_data("4100", "01" if status else "00")

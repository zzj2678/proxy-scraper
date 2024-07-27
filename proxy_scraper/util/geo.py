import logging
import random
from typing import Optional

import pycountry
import requests

logger = logging.getLogger(__name__)

GEO_NAMES_USERNAMES = ['no13bus', 'no10bus']

class GEO:
    def __init__(self):
        self.geonames_usernames = GEO_NAMES_USERNAMES

    def _get_random_username(self) -> str:
        """Return a random GeoNames username."""
        return random.choice(self.geonames_usernames)

    def _translate_country_name(self, name: str) -> Optional[str]:
        """Translate a country name to its ISO 3166-1 alpha-2 code using GeoNames API."""
        username = self._get_random_username()
        url = f"http://api.geonames.org/searchJSON?q={name}&maxRows=1&username={username}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if 'geonames' in data and data['geonames']:
                return data['geonames'][0].get('countryCode')
        except requests.RequestException as e:
            logger.error(f"Error translating country name '{name}' using GeoNames: {e}")
        return None

    def _get_country_code_from_pycountry(self, name: str) -> Optional[str]:
        """Get the ISO 3166-1 alpha-2 code using pycountry."""
        try:
            country = pycountry.countries.lookup(name)
            return country.alpha_2
        except LookupError:
            return None

    def get_country_code(self, name: str) -> Optional[str]:
        """Get the ISO 3166-1 alpha-2 code from either GeoNames or pycountry."""
        # Check if the name appears to be in Chinese (assuming any non-ASCII character is Chinese)
        if any('\u4e00' <= char <= '\u9fff' for char in name):
            country_code = self._translate_country_name(name)
        else:
            country_code = self._get_country_code_from_pycountry(name)

        if country_code:
            return country_code
        else:
            logger.warning(f"Could not normalize country name '{name}'.")
            return None

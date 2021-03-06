# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
from time import sleep

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size, try_int
from sickrage.providers import TorrentProvider


class RarbgProvider(TorrentProvider):
    def __init__(self):
        super(RarbgProvider, self).__init__("Rarbg", 'https://rarbg.to', False)

        self.urls.update({
            'api': 'https://torrentapi.org/pubapi_v2.php'
        })

        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.token_expires = None

        self.proper_strings = ['{{PROPER|REPACK|REAL|RERIP}}']

        self.cache = TVCache(self, min_time=10)

    def login(self, reset=False):
        if not reset and self.token and self.token_expires and datetime.datetime.now() < self.token_expires:
            return True

        login_params = {
            'get_token': 'get_token',
            'format': 'json',
            'app_id': 'sickrage',
        }

        try:
            response = self.session.get(self.urls['api'], params=login_params).json()
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider".format(self.name))
            return False

        self.token = response.get('token')
        self.token_expires = datetime.datetime.now() + datetime.timedelta(minutes=14) if self.token else None

        return self.token is not None

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'app_id': 'sickrage',
            'category': 'tv',
            'min_seeders': try_int(self.minseed),
            'min_leechers': try_int(self.minleech),
            'limit': 100,
            'format': 'json_extended',
            'ranked': try_int(self.ranked),
            'token': self.token,
            'sort': 'last',
            'mode': 'list',
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)

            if mode == 'RSS':
                search_params['search_string'] = None
                search_params['search_tvdb'] = None
            else:
                search_params['sort'] = self.sorting if self.sorting else 'seeders'
                search_params['mode'] = 'search'
                search_params['search_tvdb'] = ep_obj.show.indexerid

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)
                    if self.ranked:
                        sickrage.app.log.debug('Searching only ranked torrents')

                search_params['search_string'] = search_string

                # Check if token is still valid before search
                if not self.login():
                    continue

                # sleep 5 secs per request
                sleep(5)

                try:
                    data = self.session.get(self.urls['api'], params=search_params).json()
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        if data.get('error'):
            if data.get('error_code') == 4:
                if not self.login(True): return results
                return results
            elif data.get('error_code') == 5:
                return results
            elif data.get('error_code') != 20:
                sickrage.app.log.debug(data['error'])
                return results

        for item in data.get('torrent_results') or []:
            try:
                title = item['title']
                download_url = item['download']
                size = convert_size(item['size'], -1)
                seeders = item['seeders']
                leechers = item['leechers']

                if not all([title, download_url]):
                    continue

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider")

        return results

# coding=utf-8
# Author: ellmout <ellmout@ellmout.net>
# Inspired from : adaur <adaur.underground@gmail.com> (ABNormal)
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int
from sickrage.providers import NZBProvider


class Anizb(NZBProvider):
    """Nzb Provider using the open api of anizb.org for daily (rss) and backlog/forced searches."""

    def __init__(self):
        """Initialize the class."""
        super(Anizb, self).__init__('Anizb', 'https://anizb.org', False)

        # URLs
        self.urls.update({
            'api': '{base_url}/api/?q='.format(**self.urls)
        })

        # Miscellaneous Options
        self.supports_absolute_numbering = True
        self.anime_only = True
        self.search_separator = '*'

        # Cache
        self.cache = TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):
        """Start searching for anime using the provided search_strings. Used for backlog and daily."""
        results = []

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {0}'.format(mode))

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                    search_url = (self.urls['rss'], self.urls['api'] + search_string)[mode != 'RSS']

                    try:
                        response = self.session.get(search_url).text
                    except Exception:
                        sickrage.app.log.debug('No data returned from provider')
                        continue

                    if not response.text.startswith('<?xml'):
                        sickrage.app.log.info('Expected xml but got something else, is your mirror failing?')
                        continue

                    with bs4_parser(response) as html:
                        entries = html('item')
                        if not entries:
                            sickrage.app.log.info('Returned xml contained no results')
                            continue

                        for item in entries:
                            try:
                                title = item.title.get_text(strip=True)
                                download_url = item.enclosure.get('url').strip()
                                if not (title and download_url):
                                    continue

                                # description = item.find('description')
                                size = try_int(item.enclosure.get('length', -1))

                                results += [
                                    {'title': title, 'link': download_url, 'size': size}
                                ]
                            except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                                sickrage.app.log.error('Failed parsing provider.')
                                continue

            return results

    def _get_size(self, item):
        """Override the default _get_size to prevent it from extracting using the default tags."""
        return try_int(item.get('size'))

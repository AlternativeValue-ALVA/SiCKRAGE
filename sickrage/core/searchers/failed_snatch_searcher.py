# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
import threading

import sickrage
from sickrage.core import findCertainShow
from sickrage.core.common import Quality
from sickrage.core.queues.search import FailedQueueItem
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show.history import FailedHistory, History


class FailedSnatchSearcher(object):
    def __init__(self):
        self.name = "FAILEDSNATCHSEARCHER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the failed searcher, queuing selected episodes for search that have failed to snatch
        :param force: Force search
        """
        if self.amActive or sickrage.app.developer and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        # trim failed download history
        FailedHistory.trimHistory()

        sickrage.app.log.info("Searching for failed snatches")

        show = None
        failed_snatches = False

        snatched_episodes = [x['doc'] for x in sickrage.app.main_db.db.all('history', with_doc=True)
                             if x['doc']['action'] in Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER
                             and 24 >= int((datetime.datetime.now() - datetime.datetime.strptime(x['doc']['date'],
                                                                                                History.date_format)).total_seconds() / 3600) >= sickrage.app.config.failed_snatch_age]

        downloaded_releases = [(x['doc']['showid'], x['doc']['season'], x['doc']['episode']) for x in
                               sickrage.app.main_db.db.all('history', with_doc=True)
                               if x['doc']['action'] in Quality.DOWNLOADED]

        episodes = [x for x in snatched_episodes if (x['showid'], x['season'], x['episode']) not in downloaded_releases]

        for episode in episodes:
            failed_snatches = True
            if not show or int(episode["showid"]) != show.indexerid:
                show = findCertainShow(int(episode["showid"]))

            # for when there is orphaned series in the database but not loaded into our showlist
            if not show or show.paused:
                continue

            ep_obj = show.getEpisode(int(episode['season']), int(episode['episode']))
            if isinstance(ep_obj, TVEpisode):
                # put it on the queue
                sickrage.app.search_queue.put(FailedQueueItem(show, [ep_obj], True))

        if not failed_snatches:
            sickrage.app.log.info("No failed snatches found")

        self.amActive = False

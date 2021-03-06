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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from urlparse import parse_qsl

import oauth2
import twitter

import sickrage
from sickrage.notifiers import Notifiers


class TwitterNotifier(Notifiers):
    consumer_key = "vHHtcB6WzpWDG6KYlBMr8g"
    consumer_secret = "zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E"

    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

    def __init__(self):
        super(TwitterNotifier, self).__init__()
        self.name = 'twitter'

    def _notify_snatch(self, ep_name):
        if sickrage.app.config.twitter_notify_onsnatch:
            self._notifyTwitter(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def _notify_download(self, ep_name):
        if sickrage.app.config.twitter_notify_ondownload:
            self._notifyTwitter(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.twitter_notify_onsubtitledownload:
            self._notifyTwitter(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.app.config.use_twitter:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notifyTwitter(title + " - " + update_text + new_version)

    def test_notify(self):
        return self._notifyTwitter("This is a test notification from SiCKRAGE", force=True)

    def _get_authorization(self):

        signature_method_hmac_sha1 = oauth2.SignatureMethod_HMAC_SHA1()
        oauth_consumer = oauth2.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        oauth_client = oauth2.Client(oauth_consumer)

        sickrage.app.log.debug('Requesting temp token from Twitter')

        resp, content = oauth_client.request(self.REQUEST_TOKEN_URL, 'GET')

        if resp['status'] != '200':
            sickrage.app.log.error('Invalid response from Twitter requesting temp token: %s' % resp['status'])
        else:
            request_token = dict(parse_qsl(content))

            sickrage.app.config.twitter_username = request_token['oauth_token']
            sickrage.app.config.twitter_password = request_token['oauth_token_secret']

            return self.AUTHORIZATION_URL + "?oauth_token=" + request_token['oauth_token']

    def _get_credentials(self, key):
        request_token = {'oauth_token': sickrage.app.config.twitter_username,
                         'oauth_token_secret': sickrage.app.config.twitter_password,
                         'oauth_callback_confirmed': 'true'}

        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(key)

        sickrage.app.log.debug('Generating and signing request for an access token using key ' + key)

        signature_method_hmac_sha1 = oauth2.SignatureMethod_HMAC_SHA1()
        oauth_consumer = oauth2.Consumer(key=self.consumer_key, secret=self.consumer_secret)
        sickrage.app.log.debug('oauth_consumer: ' + str(oauth_consumer))
        oauth_client = oauth2.Client(oauth_consumer, token)
        sickrage.app.log.debug('oauth_client: ' + str(oauth_client))
        resp, content = oauth_client.request(self.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % key)
        sickrage.app.log.debug('resp, content: ' + str(resp) + ',' + str(content))

        access_token = dict(parse_qsl(content))
        sickrage.app.log.debug('access_token: ' + str(access_token))

        sickrage.app.log.debug('resp[status] = ' + str(resp['status']))
        if resp['status'] != '200':
            sickrage.app.log.error('The request for a token with did not succeed: ' + str(resp['status']))
            return False
        else:
            sickrage.app.log.debug('Your Twitter Access Token key: %s' % access_token['oauth_token'])
            sickrage.app.log.debug('Access Token secret: %s' % access_token['oauth_token_secret'])
            sickrage.app.config.twitter_username = access_token['oauth_token']
            sickrage.app.config.twitter_password = access_token['oauth_token_secret']
            return True

    def _send_tweet(self, message=None):

        username = self.consumer_key
        password = self.consumer_secret
        access_token_key = sickrage.app.config.twitter_username
        access_token_secret = sickrage.app.config.twitter_password

        sickrage.app.log.debug("Sending tweet: " + message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostUpdate(message.encode('utf8')[:139])
        except Exception as e:
            sickrage.app.log.error("Error Sending Tweet: {}".format(e.message))
            return False

        return True

    def _send_dm(self, message=None):

        username = self.consumer_key
        password = self.consumer_secret
        dmdest = sickrage.app.config.twitter_dmto
        access_token_key = sickrage.app.config.twitter_username
        access_token_secret = sickrage.app.config.twitter_password

        sickrage.app.log.debug("Sending DM: " + dmdest + " " + message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostDirectMessage(dmdest, message.encode('utf8')[:139])
        except Exception as e:
            sickrage.app.log.error("Error Sending Tweet (DM): {}".format(e.message))
            return False

        return True

    def _notifyTwitter(self, message='', force=False):
        prefix = sickrage.app.config.twitter_prefix

        if not sickrage.app.config.use_twitter and not force:
            return False

        if sickrage.app.config.twitter_usedm and sickrage.app.config.twitter_dmto:
            return self._send_dm(prefix + ": " + message)
        else:
            return self._send_tweet(prefix + ": " + message)

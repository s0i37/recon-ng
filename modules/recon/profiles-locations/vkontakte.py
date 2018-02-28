# packages required for framework integration
# # -*- coding: utf8 -*-
from recon.core.module import BaseModule
from datetime import datetime

class Module(BaseModule):

    meta = {
        'Name': 'Vkontakte Contact Enumerator',
        'Author': '',
        'Version': 'v0.0.1',
        'Description': '',
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL'
    }
    basevkurl = 'https://api.vk.com/method/'


    def get_vkontakte_access_token(self):
        return self.get_explicit_oauth_token(
            'vkontakte',
            'friends',
            'https://oauth.vk.com/authorize',
            'https://oauth.vk.com/access_token'
        )

    def get_photos(self, user_id, album_id, access_token):
        url = 'https://api.vk.com/method/photos.get'
        resp = self.request( url, payload = {'owner_id': user_id, 'album_id': album_id, 'access_token': access_token} )
        if resp.json.get('response'):
            for photo in resp.json['response']:
                yield photo

    def get_albums(self, user_id, access_token):
        url = 'https://api.vk.com/method/photos.getAlbums'
        resp = self.request( url, payload = {'owner_id': user_id, 'access_token': access_token} )
        if resp.json.get('response'):
            for album in resp.json['response']:
                album_id = album['aid']
                yield album_id

    def get_users_id(self, usernames):
        url = 'https://api.vk.com/method/users.get'
        resp = self.request( url, payload = { 'user_ids': ','.join(usernames) } )
        if resp.json.get('response'):
            for user in resp.json['response']:
                yield user['uid']

    def module_run(self, usernames):
        access_token = self.get_vkontakte_access_token()
        if not access_token:
            return
        
        for user_id in self.get_users_id(usernames):
            for album_id in self.get_albums(user_id, access_token):
                self.output( 'user:%s - album:%s' % (user_id, album_id) )
                for pushpin in self.get_photos(user_id, album_id, access_token):
                    if 'lat' in pushpin.keys() and 'long' in pushpin.keys():
                        source = "VK"
                        screen_name = pushpin.get('pid')
                        profile_name = pushpin.get('owner_id')
                        profile_url = "https://vk.com/id%d" % profile_name
                        for size in ['src_xxxbig','src_xxbig', 'src_xbig', 'src_big']:
                            if pushpin.get(size):
                                media_url = pushpin.get(size)
                                break
                        thumb_url = pushpin.get('src')
                        message = pushpin.get('text') or ''
                        latitude = pushpin.get('lat') or ''
                        longitude = pushpin.get('long') or ''
                        try:
                            time = datetime.fromtimestamp( pushpin.get('created') )
                        except ValueError:
                            time = datetime(1970, 1, 1)
                        
                        self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
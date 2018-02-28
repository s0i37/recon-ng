# packages required for framework integration
# # -*- coding: utf8 -*-
from recon.core.module import BaseModule
from datetime import datetime

class Module(BaseModule):

    meta = {
        'Name': 'Vkontakte Profile Enumerator',
        'Author': '@s0i37',
        'Version': 'v0.0.1',
        'Description': 'Get usernames by user_ids',
        'query': "SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL AND resource LIKE 'VK' COLLATE NOCASE"
    }
    basevkurl = 'https://api.vk.com/method/'

    def module_run(self, usernames):        
        url = 'https://api.vk.com/method/users.get'
        resp = self.request( url, payload = { 'user_ids': ','.join(usernames), 'fields': 'screen_name' } )
        if resp.json.get('response'):
            for user in resp.json['response']:
                if user.get('screen_name'):
                    username = user['screen_name']
                    name = "%s %s" % ( user.get('first_name'), user.get('last_name') )
                    self.add_profiles(username=username, resource='VK', url='https://vk.com/' + username, category='social', notes=name)
# packages required for framework integration
# # -*- coding: utf8 -*-
from recon.core.module import BaseModule

# create application (web-site)
# https://oauth.vk.com/authorize?client_id=<CLIENT_ID>&display=page&redirect_uri=http://localhost:31337recon&scope=friends&response_type=code&v=5.62
# redirect http://localhost:31337/?code=<CODE>
# https://oauth.vk.com/access_token?client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>&code=<CODE>&redirect_uri=http://localhost:31337

class Module(BaseModule):

    meta = {
        'Name': 'vk.com Profile and Contact Harvester',
        'Author': '@s0i37',
        'Version': 'v0.1',
        'Description': "Harvests profiles from vkontakte. Updates the 'contacts' and 'profiles' tables",
        'required_keys': ['vkontakte_api', 'vkontakte_secret'],
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL'
    }
    basevkurl = 'https://api.vk.com/method/'


    def get_vkontakte_access_token(self):
        return self.get_explicit_oauth_token(
            'vkontakte',
            'friends',
            'https://oauth.vk.com/authorize',
            'https://oauth.vk.com/access_token'
        )

    def module_run(self, companies):
        #self.delete_key('vkontakte_token')
        access_token = self.get_vkontakte_access_token()
        if not access_token:
            return

        for company in companies:
            self.heading(company, level=0)
            self.get_groups(company, access_token)

    def get_groups(self, company, token):
        method = 'groups.search'            
        url = self.basevkurl + method
        resp = self.request(url, payload = {'q': company, 'access_token': token, 'count': 1000, 'version': '5.92'})
        for group in resp.json['response']:
            if type(group) is not int:
                self.output( "%s (%s) - %s" % ( group['name'], group['screen_name'], 'closed' if group['is_closed'] == 1 else 'open' ) )
                self.get_contacts(group['gid'], token)

    def get_contacts(self, group_id, token):
        method = 'users.search'
        url = self.basevkurl + method
        offset = 0
        while True:
            resp = self.request(url, payload = {'group_id': group_id, 'access_token': token, 'fields': 'contacts,screen_name', 'count': 10, 'offset': offset, 'version': '5.92'})
            count = resp.json['response'][0]
            for user in resp.json['response']:
                if type(user) is not int:
                    offset += 1
                    first_name = user['first_name']
                    last_name = user['last_name']
                    uid = user['uid']
                    username = user['screen_name']
                    self.add_contacts( first_name=first_name, last_name=last_name )
                    if "id%d"%uid != username:
                        self.add_profiles( username=username, resource='VK', url='https://vk.com/' + username, category='social', notes="%s %s" % (first_name, last_name) ) 
            if offset >= count:
                break

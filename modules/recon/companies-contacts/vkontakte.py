# packages required for framework integration
# # -*- coding: utf8 -*-
from recon.core.module import BaseModule

# create application (web-site)
# https://oauth.vk.com/authorize?client_id=<CLIENT_ID>&display=page&redirect_uri=http://lo/recon&scope=friends&response_type=code&v=5.62
# redirect http://lo/recon?code=<CODE>
# https://oauth.vk.com/access_token?client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>&code=<CODE>&redirect_uri=http://lo/recon

class Module(BaseModule):

    meta = {
        'Name': 'Vkontakte Contact Enumerator',
        'Author': 'Igor Ivanov (@lctrcl)',
        'Version': 'v0.0.1',
        'Description': 'Harvests contacts from vk.com. Updates the \'contacts\' table with the results',
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
        access_token = self.get_vkontakte_access_token()
        if not access_token:
            return
        
        if self.request( self.basevkurl + "account.getInfo", payload={'access_token': access_token} ).json.get('error'):
            self.delete_key('vkontakte_token')
            access_token = self.get_vkontakte_access_token()
            if not access_token:
                return

        if self.login(access_token):
            for company in companies:
                self.heading(company, level=0)
                self.get_contacts(company, access_token)

    def login(self, token):
        if token:
            url  = self.basevkurl +  u'users.get?user_ids=1&access_token=%s' % token
            resp = self.request(url)
            if resp.status_code == 200:
                return True
        else:
            return False

    def get_contacts(self, company, token):
        method = 'users.search'
        url = self.basevkurl + method
        resp = self.request(url, payload = {'company': company, 'access_token': token, 'fields': 'contacts', 'count': 1000})
        for user in resp.json['response']:
            if type(user) is not int:
                first_name = user[u'first_name']
                last_name = user[u'last_name']
                uid = user[u'uid']
                self.output('%s %s, ID: %s' % (first_name, last_name, uid))
                self.add_contacts(first_name=first_name,  last_name=last_name)
        return

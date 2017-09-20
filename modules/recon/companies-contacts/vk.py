# packages required for framework integration
# # -*- coding: utf8 -*-
from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'Name': 'Vkontakte Contact Enumerator',
        'Author': '@s0i37',
        'Version': 'v0.0.1',
        'Description': 'Harvests contacts from vk.com via group_id. Updates the \'contacts\' table with the results.\nNo demand APIKEY.',
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL'
    }
    basevkurl = 'https://api.vk.com/method/'


    def module_run(self, companies):
        for company in companies:
            self.get_contacts(company)
            print company

    def get_contacts(self, company):
        method = 'groups.getMembers'
        url = self.basevkurl + method
        resp = self.request(url, payload = {'group_id': company, 'fields': 'first_name,last_name,bdate'})
        for user in resp.json['response']['users']:
            first_name = user.get(u'first_name')
            last_name = user.get(u'last_name')
            bdate = user.get(u'bdate') or ''
            uid = user[u'uid']
            if first_name and last_name:
                self.output('%s %s (%s), ID: %s' % (first_name, last_name, bdate, uid))
                self.add_contacts(first_name=first_name,  last_name=last_name)
        return

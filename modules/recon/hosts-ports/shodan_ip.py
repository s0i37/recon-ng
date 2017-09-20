from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Shodan IP Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53) and Matt Pluckett (@t3lc0)',
        'description': 'Harvests port information from the Shodan API by using the \'ip\' search operator. Updates the \'ports\' table with the results.',
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
        'options': (
            ('limit', 1, True, 'limit number of api requests per input source (0 = unlimited)'),
        ),
    }

    def _shodan_ports(self, ipaddr):
        url = 'https://api.shodan.io/shodan/host/{ip}'.format(ip=ipaddr)
        payload = { 'key': self.get_key('shodan_api') }
        resp = self.request(url, payload=payload)
        if resp.json != None and 'data' in resp.json.keys():
            for data in resp.json['data']:
                yield data['port']

    def module_run(self, ipaddrs):
        limit = self.options['limit']
        for ipaddr in ipaddrs:
            self.heading(ipaddr, level=0)
            for port in self._shodan_ports(ipaddr):
                self.add_ports(ip_address=ipaddr, port=port)

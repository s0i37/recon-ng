from recon.core.module import BaseModule
from time import sleep

class Module(BaseModule):

    meta = {
        'name': 'Virustotal domains extractor',
        'author': '@s0i37 (thanks @jevalenciap)',
        'description': 'Harvests domains from the Virustotal by using a report API. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL',
        'options': (
            ('interval', 15, True, 'interval in seconds between api requests'),
        ),
    }
    url = 'https://www.virustotal.com/vtapi/v2/ip-address/report'

    def module_run(self, netblocks):
        key = self.get_key('virustotal_api')
        interval = self.options['interval']
        for netblock in netblocks:
            for ip in self.cidr_to_list(netblock):
                self.heading(ip, level=0)
                resp = self.request( self.url, payload = {'ip': ip, 'apikey': key} )
                if resp.json and 'resolutions' in resp.json.keys():
                    for entry in resp.json['resolutions']:
                        hostname = entry.get('hostname')
                        if hostname:
                            self.add_hosts(host=hostname, ip_address=ip)
                sleep(interval)

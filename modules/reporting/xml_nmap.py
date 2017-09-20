from recon.core.module import BaseModule
from lxml import etree, builder
import os

class Module(BaseModule):

    meta = {
        'name': 'XML nmap report',
        'author': 's0i37',
        'version': 'v0.0.1',
        'description': 'Creates a XML nmap report. For import results in metasploit, ncrack and others',
        'options': (
            ('filename', os.path.join(BaseModule.workspace, 'results.xml'), True, 'path and filename for report output'),
        ),
    }

    def module_run(self):
        filename = self.options['filename']
        xml = builder.ElementMaker()
        with open(filename, 'wb') as o:
            xml_nmap = xml.nmaprun()
            for ip_address,_ in self.query("SELECT ip_address,1 FROM ports"):
                xml_status = xml.status( {'state':'up', 'reason':'user-set', 'reason_ttl':'0'} )
                xml_address = xml.address( {'addr':ip_address, 'addrtype':'ipv4'} )
                xml_hostnames = xml.hostnames()
                for domain,_ in self.query("SELECT host,1 FROM hosts where ip_address='%s'" % ip_address):
                    if domain:
                        xml_hostnames.insert(0, xml.hostname( {'name':domain, 'type':'PTR'} ) )                    
                xml_ports = xml.ports()
                for port,protocol in self.query("SELECT port,protocol from ports where ip_address='%s'" % ip_address):
                    xml_ports.insert( 0, xml.port( {'protocol':'tcp', 'portid':port}, xml.state( {'state':'open'} ), xml.service( {'name': protocol if not protocol is None else ''} ) ) )
                
                xml_nmap.insert( 0,
                    xml.host( xml_status, xml_address, xml_hostnames, xml_ports )
                    )

            o.write( etree.tostring(xml_nmap, xml_declaration=True) )
        self.output('ports data written to \'%s\'.' % filename)

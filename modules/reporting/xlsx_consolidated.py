from recon.core.module import BaseModule
import os
import xlsxwriter
from random import random
from socket import inet_aton, inet_ntoa
import struct
from ipwhois import IPWhois

class Module(BaseModule):

    meta = {
        'name': 'XLSX consolidated report',
        'author': 's0i37',
        'version': 'v0.1',
        'description': 'Create consolidated report with all targets, including hosts, ports, netblocks and known vulnerabilities',
        'options': (
            ('filename', os.path.join(BaseModule.workspace, 'results.xlsx' ), True, 'path and filename for output'),
        ),
    }

    def _get_netblock_range_number(self, ip_address):
        netblock_number = 0
        for netblock in self.netblocks:
            if ip_address in netblock:
                return netblock_number
            else:
                netblock_number += 1
        return netblock_number

    def _get_random_color(self):
        random_gradient_green = int( random() * (0x50) ) + 0xa0 - ( (len(self.netblocks)*0x20) % 0xa0 )
        random_gradient_blue = int( random() * (0x50) ) + 0xa0 - ( (len(self.netblocks)*0x20) % 0xa0 )
        return '#00%x%x' % (random_gradient_green, random_gradient_blue)

    def report_hosts(self, workbook):
        self.format_row_colors = []
        self.netblocks = []
        for netblock,_ in self.query("select netblock,1 from netblocks"):    
            self.netblocks.append( self.cidr_to_list(netblock) )
            self.format_row_colors.append( self._get_random_color() )
        self.format_row_colors.append( '#ffffff' ) #default color

        worksheet = workbook.add_worksheet( "hosts" )
        format_bold = workbook.add_format( {'bold': 1} )
        format_colors = []
        format_vuln = workbook.add_format()
        format_vuln.set_bg_color('red')
        for netblock_number in range( len( self.netblocks ) + 1 ):
            format = workbook.add_format()
            format.set_bg_color( self.format_row_colors[netblock_number] )
            format.set_border(1)
            format.set_text_wrap()
            format_colors.append( format )

        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 60)
        worksheet.write('A1', 'host', format_bold)
        worksheet.write('B1', 'port', format_bold)
        worksheet.write('C1', 'info', format_bold)
        row_num = 2

        ip_addresses = [ struct.unpack( "!L", inet_aton(ip) )[0] for ip,_ in self.query("SELECT ip_address,1 FROM hosts UNION SELECT ip_address,1 FROM ports") if not ip is None ]
        ip_addresses.sort()

        for ip_address in ip_addresses:
            ip_address = inet_ntoa( struct.pack("!L", ip_address) )
            format_color = format_colors[ self._get_netblock_range_number( ip_address ) ]

            #domains
            domains = [ domain for domain,_ in self.query( "SELECT DISTINCT host,1 FROM hosts WHERE ip_address='%s'" % ip_address ) if not domain is None ]
            host_info = "%(ip)s (%(domains)s)" % { 'ip': ip_address, 'domains': ', '.join(domains) }
            
            #ports
            _row_num = row_num
            for port,_ in self.query( "SELECT port,1 from (SELECT cast(port as decimal) as port FROM ports WHERE ip_address='%s') ORDER BY port" % ip_address ):
                worksheet.set_row('%d' % _row_num, 10, format_color)
                worksheet.write('B%d' % _row_num, port, format_color)
                _row_num += 1
            if _row_num > row_num + 1:
                worksheet.merge_range( 'A%d:A%d' % (row_num, _row_num-1), '', format_color )
            format_color.set_align('vcenter')

            #vulns
            vulns = [ vulns for vulns,_ in self.query( "SELECT reference,1 FROM vulnerabilities WHERE host IN (%s)" % ','.join( ["'%s'" % domain for domain in domains] ) ) ]
            if vulns:
                worksheet.write('C%d' % row_num, ';'.join(vulns), format_vuln )

            worksheet.write('A%d' % row_num, host_info, format_color)
            row_num = row_num+1 if row_num == _row_num else _row_num

        #netblocks
        row_num += 3
        netblock_number = 0
        for netblock,_ in self.query("SELECT netblock,1 FROM netblocks"):
            worksheet.set_row(row_num-1, 75)
            worksheet.write( 'A%d' % row_num, netblock, format_colors[netblock_number] )
            descriptions = []
            for net in IPWhois( self.cidr_to_list(netblock)[0] ).lookup_whois()['nets']:
                descriptions.append( net['name'] or ';'.join( str( net['description'] ).split('\n') ) )
            worksheet.merge_range( 'B%d:C%d' % (row_num,row_num), ';'.join(descriptions), format_colors[netblock_number] )
            netblock_number += 1
            row_num += 1

    def report_contacts(self, workbook):
        worksheet = workbook.add_worksheet( "contacts" )
        format_bold = workbook.add_format( {'bold': 1} )
        format_vuln = workbook.add_format()
        format_vuln.set_bg_color('red')
        emails_pwned = {}

        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 50)
        worksheet.write('A1', 'name', format_bold)
        worksheet.write('B1', 'email', format_bold)
        worksheet.write('C1', 'leak', format_bold)

        row_num = 2
        for (email,password,_hash) in self.query("SELECT username, password, hash FROM credentials"):
            (email,password,_hash) = (email, password or '', _hash or '')
            if email:
                emails_pwned[email] = ' '.join( [password, _hash] )

        for (first_name,last_name,middle_name,email) in self.query("SELECT first_name, last_name, middle_name, email FROM contacts"):
            (first_name,last_name,middle_name,email) = (first_name or '', last_name or '', middle_name or '', email or '')
            worksheet.write('A%d' % row_num, ' '.join( [first_name,last_name,middle_name] ) )
            worksheet.write('B%d' % row_num, email )
            if email in emails_pwned.keys():
                worksheet.write('C%d' % row_num, 'was leaked ' + emails_pwned[email], format_vuln )
            row_num += 1

    def module_run(self):
        filename = self.options['filename']

        with xlsxwriter.Workbook(filename, {'strings_to_urls': False}) as workbook:
            self.report_hosts(workbook)
            self.report_contacts(workbook)

        self.output( 'hosts, ports, netblocks and contacts data written to \'%s\'.' % (filename) )

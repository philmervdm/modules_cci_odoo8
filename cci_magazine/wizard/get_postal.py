##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# 2012-07-24 PVDM : CSV in Excel Format
# 2012-07-24 PVDM : manage BTE without number before it
# 2012-07-24 PVDM : translate 'CHSEE' into 'CH'
# 2012-07-24 PVDM : separated address fields available also in Excel File
# 2012-07-24 PVDM : old city in place of 'name' from zip_code un xml file
# 2012-07-24 PVDM : <organization> -> <organisation>
# 2012-07-24 PVDM : 'newspaper' -> 'magazine' in xml file
# 2012-07-25 PVDM : ' ST ' -> ' SAINT ' et ' STE ' -> ' SAINTE '
# 2012-10-08 PVDM : ajout de la colonne SubscriptionNumber au fichier CSV
# 2014-02-06 PVDM : Prise en charge temporaire gratuite de tous les premiums
# 2014-08-14 PVDM : prise en charge des abonnements au magazine

from openerp import models, fields , api , _ 

from datetime import datetime
import base64
import csv
import StringIO

CURRENT_PROSPECT = "Prospect en cours"
FUTURE_PROSPECT = "Prospect"
CLASSICAL_MEMBER = "Membre"
INDENT = '   '

form= """<?xml version="1.0"?>
<form string="Get postal sending file (SUMO)">
    <field name="method" colspan="4"/>
    <field name="editor_code"/>
    <field name="edition_code"/>
    <field name="end_date"/>
    <newline/>
    <field name="issue_id" colspan="4"/>
</form>"""

# form_fields = {
#     'method': {'string': 'Method','type':'selection','selection': [('cciconnect','CCI Connect standard'),('ccih','CCIH standard')],'required': True,'default':'cciconnect'},
#     'editor_code': {'string':'Editor Code','type':'char','size':3,'required':True},
#     'edition_code':{'string':'Edition Code','type':'char','size':4,'required':True},
#     'end_date':{'string':'Valid until','type':'date','required':True},
#     'issue_id': {'string':'Issue', 'type':'many2one', 'relation':'sale.advertising.issue','required':True},
# }

msg_form = """<?xml version="1.0"?>
<form string="File prepared">
     <separator string="File has been created."  colspan="4"/>
     <field name="msg" colspan="4" nolabel="1"/>
     <field name="postal.xml" colspan="4" />
     <field name="postal.csv" colspan="4" />
</form>"""

msg_fields = {
    'msg': {'string':'File created', 'type':'text', 'size':'100','readonly':True},
    'postal.xml':{'string': 'File for SUMO','type': 'binary','readonly': True,},
    'postal.csv':{'string': 'CSV-Excel File','type': 'binary','readonly': True,},
}

def compose_fullname(company_name,address_name):
    if company_name:
        if address_name:
            if address_name[0] == '-':
                result = company_name + ' ' + address_name
            elif address_name[0:1] == ' -':
                result = company_name + address_name
            else:
                result = address_name
        else:
            result = company_name
    else:
        # possible because can be a private address
        if address_name:
            result = address_name
        else:
            result = ''
    if result == 'Adresse personnelle':
        result = ''
    return result

def convert_xml(string):
    result = string.replace('&','&amp;')
    return result.replace('"','&quot;').replace("'",'&apos;').replace('<','&lt;').replace('>','&gt;')

def separate_street(street):
    comma = street.find(',')
    if comma > 0:
        part1 = street[0:comma].strip()
        part2 = street[comma+1:].strip()
    else:
        part1 = street
        part2 = ''
    if part2 and ( part2.find(' BTE ') > 0 or part2[0:4] == 'BTE ' ):
        if part2[0:4] == 'BTE ':
            part3 = part2[4:].strip()
            part2 = ''
        else:
            box = part2.find(' BTE' )
            part3 = part2[box+5:].strip()
            part2 = part2[0:box].strip()
    else:
        part3 = ''
    if 'CHSEE ' in part1:
        part1 = part1.replace('CHSEE ', 'CH ' )
    if ' ST ' in part1:
        part1 = part1.replace(' ST ',' SAINT ')
    if ' STE ' in part1:
        part1 = part1.replace(' STE ',' SAINTE ')
    return (part1,part2,part3)

class wizard_get_postal(models.TransientModel):
    _name = 'get.postal'
    
    method = fields.Selection([('cciconnect','CCI Connect standard'),('ccih','CCIH standard')],string = 'Method',required = True,default = 'cciconnect')
    editor_code =  fields.Char(string='Editor Code',size=3,required=True)
    edition_code = fields.Char(string='Edition Code', size=4, required=True)
    end_date =  fields.Date(string='Valid until', required=True)
    issue_id =  fields.Many2one('sale.advertising.issue', string='Issue', required=True)

    @api.multi
    def _extract_file(self):
        if self.method == 'cciconnect':
            self._extract_cciconnect()
        elif self.method == 'ccih':
            self._extract_ccih()
        return True

    @api.multi
    def _cancel_old_classical_members(self):
        # for all partners non-members, if 'ppi' or 'postal' on linked addresses or jobs with 'source' = 'Membre', we cancel these
        # subscription by putting 'prospect' in magazine_subscription and 'null' in source
        obj_partner = self.env['res.partner']
        partners = obj_partner.search([('membership_state','!=','paid'),('membership_state','!=','invoiced'),('membership_state','!=','free')])
#         partners = obj_partner.browse(cr,uid,partner_ids)
        cancel_jobs = []
        cancel_addresses = []
        for partner in partners:
            if partner.child_ids:
                for addr in partner.child_ids:
                    if addr.active:
                        if addr.magazine_subscription in ['postal','personal'] and addr.magazine_subscription_source == CLASSICAL_MEMBER:
                            cancel_addresses.append(addr)
                        if addr.other_contact_ids:
                            for job in addr.other_contact_ids:
                                if job.active and job.magazine_subscription in ['postal','personal'] and job.magazine_subscription_source == CLASSICAL_MEMBER:
                                    cancel_jobs.append(job)
        cancel_addresses.write({'magazine_subscription':'prospect','magazine_subscription_source':''})
        cancel_jobs.write({'magazine_subscription':'prospect','magazine_subscription_source':''})
        return ( len(cancel_addresses)+len(cancel_jobs) )

    @api.multi
    def _subscribe_new_members(self):
        # for all paid or invoiced member partners, if no 'ppi' and no 'postal' on linked addresses or jobs, we subscribe a job or an address
        # with 'magazine_subscription' = 'postal' and 'magazine_subscription_source' = CLASSICAL_MEMBER
        obj_partner = self.env['res.partner']
        partners = obj_partner.search([('membership_state','in',['paid','invoiced'])])
#         partners = obj_partner.browse(cr,uid,partner_ids)
        new_jobs = []
        new_addresses = []
        for partner in partners:
            new_subscriber = False
            if partner.child_ids:
                new_subscriber = True
                for addr in partner.child_ids:
                    if addr.active:
                        if addr.magazine_subscription in ['postal','personal']:
                            new_subscriber = False
                            break
                        if addr.other_contact_ids:
                            for job in addr.other_contact_ids:
                                if job.active and job.magazine_subscription in ['postal','personal']:
                                    new_subscriber = False
            if new_subscriber: # has address(es) and perhaps jobs but none has 'postal' or 'personal'
                               # =>search for one job or one address to subscribe
                # search for the first possible address : first, 'default', then 'invoice', then 'other'
                foundAddr = False
                for addr in partner.child_ids:
                    if addr.type == 'default' and addr.magazine_subscription != 'never' and addr.zip_id and not addr.notdelivered:
                        foundAddr = addr
                        break
                if not foundAddr:
                    for addr in partner.child_ids:
                        if addr.type == 'invoice' and addr.magazine_subscription != 'never' and addr.zip_id and not addr.notdelivered:
                            foundAddr = addr
                            break
                if not foundAddr:
                    current_sequence = 9999
                    for addr in partner.child_ids:
                        if addr.type == 'other' and addr.magazine_subscription != 'never' and addr.zip_id and not addr.notdelivered:
                            if ( addr.sequence_partner or 0 ) and ( addr.sequence_partner or 0 ) < current_sequence:
                                foundAddr = addr
                                current_sequence = ( addr.sequence_partner or 0 )
                
                foundJob = False
                if foundAddr and foundAddr.other_contact_ids:
                    # inside this address, we search for a good job : first '1', then 'G', then others by importance of sequence
                    current_sequence = 9999
                    for job in foundAddr.other_contact_ids:
                        if job.contact_id and job.function_code_label and '1' in job.function_code_label:
                            if ( job.sequence_partner or 0 ) and ( job.sequence_partner or 0 ) < current_sequence:
                                foundJob = job
                                current_sequence = ( job.sequence_partner or 0 )
                    if not foundJob:
                        for job in foundAddr.other_contact_ids:
                            if job.contact_id and job.function_code_label and 'G' in ( job.function_code_label or '' ):
                                if ( job.sequence_partner or 0 ) and ( job.sequence_partner or 0 ) < current_sequence:
                                    foundJob = job
                                    current_sequence = ( job.sequence_partner or 0 )
                    if not foundJob:
                        for job in foundAddr.other_contact_ids:
                            if job.contact_id:
                                if ( job.sequence_partner or 0 ) and ( job.sequence_partner or 0 ) < current_sequence:
                                    foundJob = job
                                    current_sequence = ( job.sequence_partner or 0 )
                if foundAddr:
                    if foundJob:
                        new_jobs.append(foundJob)
                    else:
                        new_addresses.append(foundAddr)
                        
        new_addresses.write({'magazine_subscription':'postal','magazine_subscription_source':CLASSICAL_MEMBER})
        new_jobs.write({'magazine_subscription':'postal','magazine_subscription_source':CLASSICAL_MEMBER})
        return ( len(new_addresses)+len(new_jobs) )
    
    @api.multi
    def _extract_cciconnect(self):
        try: ### to capture the possible error of transcripting caracters to cp1252
        #if True:
            count_lines = 0  ## count the number of lines in the final file to show to the user
            canceled = 0 ## count the number of canceled sending because not more usefull
            new_subscriber = 0 ## count the number of new subscribers because paid or invoiced members
            #
            canceled = self._cancel_old_classical_members()
            new_subscriber = self._subscribe_new_members()
            #
            sended_contacts = []  ## list of id of contacts in the final file. The same id can't exists two times
            sended_addresses = [] ## list of id of addresses in the final file. Possible, under certains circumstances, that an id exists several times if this list
            
            now =  fields.Datetime.now()  #datetime.datetime.now()
            in2days =  now +  datetime.timedelta(days=2)
            cEndDate = self.end_date + ' 23:59:59'

            csvfile=StringIO.StringIO()
            xmlfile=StringIO.StringIO()
            hfCSV = csv.writer(csvfile,delimiter=";",quotechar='"',quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n')
            hfCSV.writerow(['firstname','lastname','courtesy','persoemail','mobile','profphone','proffax','profemail','function',
                            'function_codes','adrtype','adrname','adrstreet','adrstreet2','adrcity','adremail','company','company_legal','name',
                            'onlystreet', 'onlynumber', 'onlybox', 'contact_id','job_id','address_id','partner_id','origin',
                            'addr_magazine_subscription','addr_magazine_source','job_magazine_subscription','job_magazine_source','subscription_number'])
            xmlfile.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
            xmlfile.write('<!DOCTYPE BePostSubscriptionDistribution SYSTEM "C:\BePostSubscriptionDistribution.dtd">\n')
            xmlfile.write('<BePostSubscriptionDistribution Identification="%s" TimeDateStamp="%s">\n' % ('CCIMag_SUMO_' + now.strftime('%Y-%m-%d_%H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')) )
            xmlfile.write(INDENT + ( '<Editor Code="%s"/>\n' % data['form']['editor_code'] ) )
            # step 1. Extract the job with 'postal'
            obj_job = self.env['res.partner']
            jobs = obj_job.search([('magazine_subscription','=','postal')])
#             if job_ids:
#                 jobs = obj_job.browse(cr,uid,job_ids)
#             else:
#                 jobs = []
            
            for job in jobs:
                if job.contact_id and job.address_id:
                    if ( job.contact_id.id not in sended_contacts ) and ( job.contact_id.active ) and \
                       ( job.address_id.active ) and ( not job.address_id.notdelivered ) and job.address_id.zip_id.id:
                        # the contact person is OK and the address is valid 
                        lContinue = True
                        if job.address_id.partner_id and job.address_id.partner_id.state_id.id != 1:
                            lContinue = False
                        if lContinue: # either no partner (private address) or active partner
                            (streetname,streetnumber,streetbox) = separate_street( job.address_id.street or '' )
                            record = []
                            record.append( ( job.contact_id.first_name or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.name or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.title or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.email or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.mobile or '' ).encode('cp1252') )
                            record.append( ( job.phone or '' ).encode('cp1252') )
                            record.append( ( job.fax or '' ).encode('cp1252') )
                            record.append( ( job.email or '' ).encode('cp1252') )
                            record.append( ( job.function_label or '' ).encode('cp1252') )
                            record.append( ( job.function_code_label or '' ).encode('cp1252') )
                            record.append( ( job.address_id.type or '' ).encode('cp1252') )
                            if job.address_id.name and job.address_id.name[0] == '-':
                                record.append( ( ' ' + job.address_id.name ).encode('cp1252') )
                            else:
                                record.append( ( job.address_id.name or '' ).encode('cp1252') )
                            record.append( ( job.address_id.street or '' ).encode('cp1252') )
                            record.append( ( job.address_id.street2 or '' ).encode('cp1252') )
                            if job.address_id.zip_id.name == 'manuel':
                                record.append( job.address_id.zip_id.city.encode('cp1252') )
                            else:
                                record.append( ( job.address_id.zip_id.name + ' ' + job.address_id.zip_id.city ).encode('cp1252') )
                            record.append( ( job.address_id.email or '' ).encode('cp1252') )
                            if job.address_id.partner_id:
                                record.append( job.address_id.partner_id.name.encode('cp1252') )
                                record.append( ( job.address_id.partner_id.title or '' ).encode('cp1252') )
                                record.append( compose_fullname( job.address_id.partner_id.name, job.address_id.name ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                                record.append( compose_fullname( '', job.address_id.name ).encode('cp1252') )
                            record.append( (streetname or '').encode('cp1252') )
                            record.append( (streetnumber or '').encode('cp1252') )
                            record.append( (streetbox or '').encode('cp1252') )
                            record.append( job.contact_id.id )
                            record.append( job.id )
                            record.append( job.address_id.id )
                            if job.address_id.partner_id:
                                record.append( job.address_id.partner_id.id )
                            else:
                                record.append( 0 )
                            record.append( 'job-postal' )
                            record.append( ( job.address_id.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( job.address_id.magazine_subscription_source or '' ).encode('cp1252') )
                            record.append( ( job.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( job.magazine_subscription_source or '' ).encode('cp1252') )
                            record.append( 'J' + str(job.id ) )
                            hfCSV.writerow(record)
                            #
                            xmlfile.write(INDENT + '<AddMagazineSubscription StartDate="%s" EndDate="%s">\n' % (in2days.strftime('%Y-%m-%d %H:%M:%S'),cEndDate) )
                            xmlfile.write(INDENT + INDENT + '<SubscriptionNumber EditionCode="%s">%s</SubscriptionNumber>\n' % ( data['form']['edition_code'],"J"+str(job.id)) )
                            xmlfile.write(INDENT + INDENT + '<Subscriber>\n' )
                            if job.address_id.partner_id:
                                organization_name = compose_fullname( job.address_id.partner_id.name, job.address_id.name )
                            else:
                                organization_name = compose_fullname( '', job.address_id.name )
                            xmlfile.write(INDENT + INDENT + INDENT + '<Organisation>%s</Organisation>\n' % convert_xml( organization_name ) )
                            xmlfile.write(INDENT + INDENT + INDENT + '<Salutation>%s</Salutation>\n' % convert_xml( job.contact_id.title or '' ) )
                            xmlfile.write(INDENT + INDENT + INDENT + '<FirstName>%s</FirstName>\n' % convert_xml( job.contact_id.first_name or '' ) )
                            xmlfile.write(INDENT + INDENT + INDENT + '<LastName>%s</LastName>\n' % convert_xml( job.contact_id.name or '' ) )
                            xmlfile.write(INDENT + INDENT + '</Subscriber>\n' )
                            xmlfile.write(INDENT + INDENT + '<Address>\n' )
                            xmlfile.write(INDENT + INDENT + INDENT + '<StreetName>%s</StreetName>\n' % convert_xml( streetname ) )
                            if streetnumber:
                                xmlfile.write(INDENT + INDENT + INDENT + '<HouseNumber>%s</HouseNumber>\n' % convert_xml( streetnumber ) )
                            if streetbox:
                                xmlfile.write(INDENT + INDENT + INDENT + '<Box>%s</Box>\n' % convert_xml( streetbox ) )
                            xmlfile.write(INDENT + INDENT + INDENT + '<ZipCode>%s</ZipCode>\n' % convert_xml( job.address_id.zip_id.name ) )
                            xmlfile.write(INDENT + INDENT + INDENT + '<MunicipalityName>%s</MunicipalityName>\n' % convert_xml( job.address_id.zip_id.old_city or job.address_id.zip_id.city ) )
                            xmlfile.write(INDENT + INDENT + '</Address>\n' )
                            xmlfile.write(INDENT + INDENT + '<NumberOfPieces>1</NumberOfPieces>\n' )
                            xmlfile.write(INDENT + '</AddMagazineSubscription>\n' )
                            #
                            count_lines += 1
                            sended_contacts.append( job.contact_id.id )
                            sended_addresses.append( job.address_id.id )

            # step 2. Extract the addresses
            obj_addr = self.env['res.partner']
            addresses = obj_addr.search([('magazine_subscription','=','postal')])
#             if addr_ids:
#                 addresses = obj_addr.browse(cr,uid,addr_ids)
#             else:
#                 addresses = []
            if addresses:
                for addr in addresses:
                    if addr.zip_id and not addr.notdelivered and ( addr.id not in sended_addresses ):
                        lContinue = True
                        if addr.partner_id and addr.partner_id.state_id.id != 1:
                            lContinue = False
                        if lContinue: # either no partner (private address) or active partner
                            # we search for the first '1' of the first 'G' or the first one in the partner_sequenced order
                            current_job = False
                            if addr.other_contact_ids:
                                current_sequence = 999999
                                for job in addr.other_contact_ids:
                                    if ( '1' in ( job.function_code_label or '' ) ) and job.contact_id and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                        if job.sequence_partner < current_sequence:
                                            current_job = job
                                            current_sequence = job.sequence_partner
                                if not current_job:
                                    for job in addr.other_contact_ids:
                                        if ( 'G' in ( job.function_code_label or '' ) ) and job.contact_id and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                            if job.sequence_partner < current_sequence:
                                                current_job = job
                                                current_sequence = job.sequence_partner
                                if not current_job:
                                    for job in addr.other_contact_ids:
                                        if job.contact_id and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                            if job.sequence_partner < current_sequence:
                                                current_job = job
                                                current_sequence = job.sequence_partner
                            record = []
                            if current_job:
                                (streetname,streetnumber,streetbox) = separate_street( addr.street or '' )
                                record.append( ( current_job.contact_id.first_name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.title or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.email or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.mobile or '' ).encode('cp1252') )
                                record.append( ( current_job.phone or '' ).encode('cp1252') )
                                record.append( ( current_job.fax or '' ).encode('cp1252') )
                                record.append( ( current_job.email or '' ).encode('cp1252') )
                                record.append( ( current_job.function_label or '' ).encode('cp1252') )
                                record.append( ( current_job.function_code_label or '' ).encode('cp1252') )
                                record.append( ( job.address_id.type or '' ).encode('cp1252') )
                                if addr.name and addr.name[0] == '-':
                                    record.append( ( ' ' + addr.name ).encode('cp1252') )
                                else:
                                    record.append( ( addr.name or '' ).encode('cp1252') )
                                record.append( ( addr.street or '' ).encode('cp1252') )
                                record.append( ( addr.street2 or '' ).encode('cp1252') )
                                if addr.zip_id.name == 'manuel':
                                    record.append( addr.zip_id.city.encode('cp1252') )
                                else:
                                    record.append( ( addr.zip_id.name + ' ' + addr.zip_id.city ).encode('cp1252') )
                                record.append( ( addr.email or '' ).encode('cp1252') )
                                if addr.partner_id:
                                    record.append( addr.partner_id.name.encode('cp1252') )
                                    record.append( ( addr.partner_id.title or '' ).encode('cp1252') )
                                    record.append( compose_fullname( addr.partner_id.name, addr.name ).encode('cp1252') )
                                else:
                                    record.append( '' )
                                    record.append( '' )
                                    record.append( compose_fullname( '', addr.name ).encode('cp1252') )
                                record.append( (streetname or '').encode('cp1252') )
                                record.append( (streetnumber or '').encode('cp1252') )
                                record.append( (streetbox or '').encode('cp1252') )
                                record.append( current_job.contact_id.id )
                                record.append( current_job.id )
                                record.append( addr.id )
                                if addr.partner_id:
                                    record.append( addr.partner_id.id )
                                else:
                                    record.append( 0 )
                                record.append( 'addr-postal' )
                                record.append( ( addr.magazine_subscription or '' ).encode('cp1252') )
                                record.append( ( addr.magazine_subscription_source or '' ).encode('cp1252') )
                                record.append( ( current_job.magazine_subscription or '' ).encode('cp1252') )
                                record.append( ( current_job.magazine_subscription_source or '' ).encode('cp1252') )
                                record.append( 'A' + str(addr.id) )
                                hfCSV.writerow( record )
                                #
                                xmlfile.write(INDENT + '<AddMagazineSubscription StartDate="%s" EndDate="%s">\n' % (in2days.strftime('%Y-%m-%d %H:%M:%S'),cEndDate) )
                                xmlfile.write(INDENT + INDENT + '<SubscriptionNumber EditionCode="%s">%s</SubscriptionNumber>\n' % ( data['form']['edition_code'],"A"+str(addr.id)) )
                                xmlfile.write(INDENT + INDENT + '<Subscriber>\n' )
                                if current_job.address_id.partner_id:
                                    organization_name = compose_fullname( current_job.address_id.partner_id.name, current_job.address_id.name )
                                else:
                                    organization_name = compose_fullname( '', current_job.address_id.name )
                                xmlfile.write(INDENT + INDENT + INDENT + '<Organisation>%s</Organisation>\n' % convert_xml( organization_name ) )
                                xmlfile.write(INDENT + INDENT + INDENT + '<Salutation>%s</Salutation>\n' % convert_xml( current_job.contact_id.title or '' ) )
                                xmlfile.write(INDENT + INDENT + INDENT + '<FirstName>%s</FirstName>\n' % convert_xml( current_job.contact_id.first_name or '' ) )
                                xmlfile.write(INDENT + INDENT + INDENT + '<LastName>%s</LastName>\n' % convert_xml( current_job.contact_id.name or '' ) )
                                xmlfile.write(INDENT + INDENT + '</Subscriber>\n' )
                                xmlfile.write(INDENT + INDENT + '<Address>\n' )
                                xmlfile.write(INDENT + INDENT + INDENT + '<StreetName>%s</StreetName>\n' % convert_xml( streetname ) )
                                if streetnumber:
                                    xmlfile.write(INDENT + INDENT + INDENT + '<HouseNumber>%s</HouseNumber>\n' % convert_xml( streetnumber ) )
                                if streetbox:
                                    xmlfile.write(INDENT + INDENT + INDENT + '<Box>%s</Box>\n' % convert_xml( streetbox ) )
                                xmlfile.write(INDENT + INDENT + INDENT + '<ZipCode>%s</ZipCode>\n' % convert_xml( current_job.address_id.zip_id.name ) )
                                xmlfile.write(INDENT + INDENT + INDENT + '<MunicipalityName>%s</MunicipalityName>\n' % convert_xml( addr.zip_id.old_city or addr.zip_id.city ) )
                                xmlfile.write(INDENT + INDENT + '</Address>\n' )
                                xmlfile.write(INDENT + INDENT + '<NumberOfPieces>1</NumberOfPieces>\n' )
                                xmlfile.write(INDENT + '</AddMagazineSubscription>\n' )
                                #
                                count_lines += 1
                                if current_job:
                                    sended_contacts.append( current_job.contact_id.id )
                                sended_addresses.append( addr.id )

            # step 3. extract the contact_id with active subscriptions
            # we extract them before extracting the free to begin to count their sended issues
            count_premiums = 0
            param_values = self.env['ir.config_parameter'].get_param('PremiumMagMode')
            if "Subscription" in param_values:
                obj_sub_type = self.env['premium_subscription.type']
                type_ids = obj_sub_type.search([('code','=','CCIMAG')])
                if type_ids:
                    # first we delete all possible previous sending to the same issue because we extract themn again...
                    close_message = "Auto Last Issue"
                    obj_contact = self.env['res.partner']
                    zip_obj = self.env['res.partner.zip']
                    issue_obj = self.env['sale.advertising.issue']
                    issue = self.issue_id.read(['name'])[0]
                    issue_name = issue['name']
                    usage_obj = self.env['premium_subscription.usage']
                    obj_sub = self.env['premium_subscription']
                    usages = usage_obj.search([('issue_id','=',self.issue_id.id)])
                    if usages:
#                         usages = usage_obj.browse(cr,uid,usage_ids)
                        for use in usages:
                            if use.subscription_id:
                                if use.subscription_id.close_source == close_message:
                                    # reactivate the subscription
                                    obj_sub.button_current([use.subscription_id.id])
                                use.subscription_id.write({'left_usages':use.subscription_id.left_usages + 1})
                                use.write({'active':False})
                            else:
                                # usage without subscription_id : delete it
                                use.unlink()
                                
                    # then we re-extract the subscription for this issue
                    sub_ids = obj_sub.search([('state','=','current'),('type_id','in',type_ids),('left_usages','>',0),('begin','<=',datetime.datetime.today().strftime('%Y-%m-%d'))])
                    subs = sub_ids.read(['contact_id','left_usages','state','specific_name','specific_street','specific_street2','specific_zip_id','specific_country_id'])
                    dSubscribers = {}
                    contact_ids =  []
                    for subscription in subs:
                        if subscription['contact_id'] and subscription['contact_id'][0] not in contact_ids:
                            dSubscribers[subscription['contact_id'][0]] = subscription
                            contact_ids.append(subscription['contact_id'][0])
                    #
                    if contact_ids:
                        contacts = obj_contact.browse(contact_ids)
                    else:
                        contacts = []
                        
                    for contact in contacts:
                        if contact.active:
                            # we mark the sended issue, now, event if the sending doesn't come from 'subscription' directly
                            if dSubscribers.has_key(contact.id):
                                subscription = dSubscribers[contact.id]
                                data_usage = {}
                                data_usage['name'] = '%s pour %s %s' % (issue_name or '', contact.name, contact.first_name or '')
                                data_usage['issue_id'] = data['form']['issue_id']
                                data_usage['subscription_id'] = subscription['id']
                                usage_obj.create(data_usage)
                                left_usages = subscription['left_usages']-1
                                obj_sub.browse(subscription['id']).write({'left_usages':left_usages})
                                if left_usages <= 0:
                                    obj_sub.browse(subscription['id']).button_close()
                                # we prepare the sending address
                                if subscription['specific_name'] or subscription['specific_street']:
                                    count_premiums += 1
                                    (streetname,streetnumber,streetbox) = separate_street( subscription['specific_street'] or '' )
                                    if subscription['specific_zip_id']:
                                        zip_data = zip_obj.read([subscription['specific_zip_id'][0]],['name','city'])[0]
                                    else:
                                        zip_data = {'name':'','city':''}
                                    record = []
                                    record.append( ( contact.first_name or '' ).encode('cp1252') )
                                    record.append( ( contact.name or '' ).encode('cp1252') )
                                    record.append( ( contact.title or '' ).encode('cp1252') )
                                    record.append( ( contact.email or '' ).encode('cp1252') )
                                    record.append( ( contact.mobile or '' ).encode('cp1252') )
                                    record.append('')
                                    record.append('')
                                    record.append('')
                                    record.append('')
                                    record.append('')
                                    record.append('specific')
                                    record.append((subscription['specific_name'] or '').encode('cp1252') )
                                    record.append((subscription['specific_street'] or '').encode('cp1252') )
                                    record.append((subscription['specific_street2'] or '').encode('cp1252') )
                                    if zip_data['name'] == 'manuel':
                                        record.append(zip_data['city'].encode('cp1252') )
                                    else:
                                        record.append( ( zip_data['name'] + ' ' + zip_data['city'] ).encode('cp1252') )
                                    record.append('')
                                    record.append('')
                                    record.append('')
                                    record.append((subscription['specific_name'] or '').encode('cp1252') )
                                    record.append((streetname or '').encode('cp1252') )
                                    record.append((streetnumber or '').encode('cp1252') )
                                    record.append((streetbox or '').encode('cp1252') )
                                    record.append(contact.id )
                                    record.append(0)
                                    record.append(0)
                                    record.append(0)
                                    record.append('premium subscription')
                                    record.append('')
                                    record.append('')
                                    record.append('')
                                    record.append('')
                                    record.append('SUB' + str(subscription['id']) )
                                    hfCSV.writerow(record)
                                    #
                                    xmlfile.write(INDENT + '<AddMagazineSubscription StartDate="%s" EndDate="%s">\n' % (in2days.strftime('%Y-%m-%d %H:%M:%S'),cEndDate) )
                                    xmlfile.write(INDENT + INDENT + '<SubscriptionNumber EditionCode="%s">%s</SubscriptionNumber>\n' % ( data['form']['edition_code'],"C"+str(contact.id)) )
                                    xmlfile.write(INDENT + INDENT + '<Subscriber>\n' )
                                    organization_name = (subscription['specific_name'] or '')
                                    xmlfile.write(INDENT + INDENT + INDENT + '<Organisation>%s</Organisation>\n' % convert_xml( organization_name ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<Salutation>%s</Salutation>\n' % convert_xml( contact.title or '' ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<FirstName>%s</FirstName>\n' % convert_xml( contact.first_name or '' ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<LastName>%s</LastName>\n' % convert_xml( contact.name or '' ) )
                                    xmlfile.write(INDENT + INDENT + '</Subscriber>\n' )
                                    xmlfile.write(INDENT + INDENT + '<Address>\n' )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<StreetName>%s</StreetName>\n' % convert_xml( streetname ) )
                                    if streetnumber:
                                        xmlfile.write(INDENT + INDENT + INDENT + '<HouseNumber>%s</HouseNumber>\n' % convert_xml( streetnumber ) )
                                    if streetbox:
                                        xmlfile.write(INDENT + INDENT + INDENT + '<Box>%s</Box>\n' % convert_xml( streetbox ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<ZipCode>%s</ZipCode>\n' % convert_xml( zip_data['name'] ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<MunicipalityName>%s</MunicipalityName>\n' % convert_xml( zip_data['city'] ) )
                                    xmlfile.write(INDENT + INDENT + '</Address>\n' )
                                    xmlfile.write(INDENT + INDENT + '<NumberOfPieces>1</NumberOfPieces>\n' )
                                    xmlfile.write(INDENT + '</AddMagazineSubscription>\n' )
                                    #
                                    count_lines += 1
                                    sended_contacts.append( contact.id )
                                else:
                                    if contact.id not in sended_contacts:
                                        # we search for the first good address with or without attached partner
                                        if contact.job_ids:
                                            found_job = False
                                            current_job_seq = 9999
                                            for job in contact.job_ids:
                                                if job.active and job.address_id and job.address_id.active and ( not job.address_id.notdelivered ) and job.address_id.zip_id and job.address_id.zip_id.id:
                                                    if job.sequence_contact < current_job_seq:
                                                        found_job = job
                                                        current_job_seq = job.sequence_contact
                                            if found_job:
                                                # the contact person is OK, has a job and the address is valid 
                                                lContinue = True
                                                if found_job.address_id.partner_id and found_job.address_id.partner_id.state_id.id != 1:
                                                    lContinue = False
                                                if lContinue: # either no partner (private address) or active partner
                                                    count_premiums += 1
                                                    (streetname,streetnumber,streetbox) = separate_street( found_job.address_id.street or '' )
                                                    record = []
                                                    record.append( ( contact.first_name or '' ).encode('cp1252') )
                                                    record.append( ( contact.name or '' ).encode('cp1252') )
                                                    record.append( ( contact.title or '' ).encode('cp1252') )
                                                    record.append( ( contact.email or '' ).encode('cp1252') )
                                                    record.append( ( contact.mobile or '' ).encode('cp1252') )
                                                    record.append( ( found_job.phone or '' ).encode('cp1252') )
                                                    record.append( ( found_job.fax or '' ).encode('cp1252') )
                                                    record.append( ( found_job.email or '' ).encode('cp1252') )
                                                    record.append( ( found_job.function_label or '' ).encode('cp1252') )
                                                    record.append( ( found_job.function_code_label or '' ).encode('cp1252') )
                                                    record.append( ( found_job.address_id.type or '' ).encode('cp1252') )
                                                    if found_job.address_id.name and found_job.address_id.name[0] == '-':
                                                        record.append( ( ' ' + found_job.address_id.name ).encode('cp1252') )
                                                    else:
                                                        record.append( ( found_job.address_id.name or '' ).encode('cp1252') )
                                                    record.append( ( found_job.address_id.street or '' ).encode('cp1252') )
                                                    record.append( ( found_job.address_id.street2 or '' ).encode('cp1252') )
                                                    if found_job.address_id.zip_id.name == 'manuel':
                                                        record.append( found_job.address_id.zip_id.city.encode('cp1252') )
                                                    else:
                                                        record.append( ( found_job.address_id.zip_id.name + ' ' + found_job.address_id.zip_id.city ).encode('cp1252') )
                                                    record.append( ( found_job.address_id.email or '' ).encode('cp1252') )
                                                    if found_job.address_id.partner_id:
                                                        record.append( found_job.address_id.partner_id.name.encode('cp1252') )
                                                        record.append( ( found_job.address_id.partner_id.title or '' ).encode('cp1252') )
                                                        record.append( compose_fullname( found_job.address_id.partner_id.name, found_job.address_id.name ).encode('cp1252') )
                                                    else:
                                                        record.append( '' )
                                                        record.append( '' )
                                                        record.append( compose_fullname( '', found_job.address_id.name ).encode('cp1252') )
                                                    record.append( (streetname or '').encode('cp1252') )
                                                    record.append( (streetnumber or '').encode('cp1252') )
                                                    record.append( (streetbox or '').encode('cp1252') )
                                                    record.append( contact.id )
                                                    record.append( found_job.id )
                                                    record.append( found_job.address_id.id )
                                                    if found_job.address_id.partner_id:
                                                        record.append( found_job.address_id.partner_id.id )
                                                    else:
                                                        record.append( 0 )
                                                    record.append( 'premium subscription' )
                                                    record.append( ( found_job.address_id.magazine_subscription or '' ).encode('cp1252') )
                                                    record.append( ( found_job.address_id.magazine_subscription_source or '' ).encode('cp1252') )
                                                    record.append( ( found_job.magazine_subscription or '' ).encode('cp1252') )
                                                    record.append( ( found_job.magazine_subscription_source or '' ).encode('cp1252') )
                                                    record.append( 'C' + str(found_job.id ) )
                                                    hfCSV.writerow(record)
                                                    #
                                                    xmlfile.write(INDENT + '<AddMagazineSubscription StartDate="%s" EndDate="%s">\n' % (in2days.strftime('%Y-%m-%d %H:%M:%S'),cEndDate) )
                                                    xmlfile.write(INDENT + INDENT + '<SubscriptionNumber EditionCode="%s">%s</SubscriptionNumber>\n' % ( data['form']['edition_code'],"C"+str(contact.id)) )
                                                    xmlfile.write(INDENT + INDENT + '<Subscriber>\n' )
                                                    if found_job.address_id.partner_id:
                                                        organization_name = compose_fullname( found_job.address_id.partner_id.name, found_job.address_id.name )
                                                    else:
                                                        organization_name = compose_fullname( '', found_job.address_id.name )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<Organisation>%s</Organisation>\n' % convert_xml( organization_name ) )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<Salutation>%s</Salutation>\n' % convert_xml( contact.title or '' ) )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<FirstName>%s</FirstName>\n' % convert_xml( contact.first_name or '' ) )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<LastName>%s</LastName>\n' % convert_xml( contact.name or '' ) )
                                                    xmlfile.write(INDENT + INDENT + '</Subscriber>\n' )
                                                    xmlfile.write(INDENT + INDENT + '<Address>\n' )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<StreetName>%s</StreetName>\n' % convert_xml( streetname ) )
                                                    if streetnumber:
                                                        xmlfile.write(INDENT + INDENT + INDENT + '<HouseNumber>%s</HouseNumber>\n' % convert_xml( streetnumber ) )
                                                    if streetbox:
                                                        xmlfile.write(INDENT + INDENT + INDENT + '<Box>%s</Box>\n' % convert_xml( streetbox ) )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<ZipCode>%s</ZipCode>\n' % convert_xml( found_job.address_id.zip_id.name ) )
                                                    xmlfile.write(INDENT + INDENT + INDENT + '<MunicipalityName>%s</MunicipalityName>\n' % convert_xml( found_job.address_id.zip_id.old_city or found_job.address_id.zip_id.city ) )
                                                    xmlfile.write(INDENT + INDENT + '</Address>\n' )
                                                    xmlfile.write(INDENT + INDENT + '<NumberOfPieces>1</NumberOfPieces>\n' )
                                                    xmlfile.write(INDENT + '</AddMagazineSubscription>\n' )
                                                    #
                                                    count_lines += 1
                                                    sended_contacts.append( contact.id )
                                                    sended_addresses.append( found_job.address_id.id )
                        else:
                            # contact no more active => desactivate also the subscription
                            if dSubscribers.has_key(contact.id):
                                obj_sub.write(cr,uid,[dSubscriber[contact.id]['id']],{'state':'cancel','close_date':datetime.datetime.today().strftime('%Y-%m-%d'),'close_user_id':False,'close_source':'Auto cancel inactive'})


                                        
            # step 4. TEMPORARY. Extract the premium contacts
            if param_values.has_key('PremiumMagMode') and 'Free' in param_values['PremiumMagMode']:
                obj_contact = pooler.get_pool(cr.dbname).get('res.partner.contact')
                contact_ids = obj_contact.search(cr,uid,[('is_premium','=','OUI')])
                if contact_ids:
                    contacts = obj_contact.browse(cr,uid,contact_ids)
                else:
                    contacts = []
                for contact in contacts:
                    if contact.id not in sended_contacts and contact.active:
                        # we search for the first good address with or without attached partner
                        if contact.job_ids:
                            found_job = False
                            current_job_seq = 9999
                            for job in contact.job_ids:
                                if job.active and job.address_id and job.address_id.active and ( not job.address_id.notdelivered ) and job.address_id.zip_id and job.address_id.zip_id.id:
                                    if job.sequence_contact < current_job_seq:
                                        found_job = job
                                        current_job_seq = job.sequence_contact
                            if found_job:
                                # the contact person is OK, has a job and the address is valid 
                                lContinue = True
                                if found_job.address_id.partner_id and found_job.address_id.partner_id.state_id.id != 1:
                                    lContinue = False
                                if lContinue: # either no partner (private address) or active partner
                                    count_premiums += 1
                                    (streetname,streetnumber,streetbox) = separate_street( found_job.address_id.street or '' )
                                    record = []
                                    record.append( ( contact.first_name or '' ).encode('cp1252') )
                                    record.append( ( contact.name or '' ).encode('cp1252') )
                                    record.append( ( contact.title or '' ).encode('cp1252') )
                                    record.append( ( contact.email or '' ).encode('cp1252') )
                                    record.append( ( contact.mobile or '' ).encode('cp1252') )
                                    record.append( ( found_job.phone or '' ).encode('cp1252') )
                                    record.append( ( found_job.fax or '' ).encode('cp1252') )
                                    record.append( ( found_job.email or '' ).encode('cp1252') )
                                    record.append( ( found_job.function_label or '' ).encode('cp1252') )
                                    record.append( ( found_job.function_code_label or '' ).encode('cp1252') )
                                    record.append( ( found_job.address_id.type or '' ).encode('cp1252') )
                                    if found_job.address_id.name and found_job.address_id.name[0] == '-':
                                        record.append( ( ' ' + found_job.address_id.name ).encode('cp1252') )
                                    else:
                                        record.append( ( found_job.address_id.name or '' ).encode('cp1252') )
                                    record.append( ( found_job.address_id.street or '' ).encode('cp1252') )
                                    record.append( ( found_job.address_id.street2 or '' ).encode('cp1252') )
                                    if found_job.address_id.zip_id.name == 'manuel':
                                        record.append( found_job.address_id.zip_id.city.encode('cp1252') )
                                    else:
                                        record.append( ( found_job.address_id.zip_id.name + ' ' + found_job.address_id.zip_id.city ).encode('cp1252') )
                                    record.append( ( found_job.address_id.email or '' ).encode('cp1252') )
                                    if found_job.address_id.partner_id:
                                        record.append( found_job.address_id.partner_id.name.encode('cp1252') )
                                        record.append( ( found_job.address_id.partner_id.title or '' ).encode('cp1252') )
                                        record.append( compose_fullname( found_job.address_id.partner_id.name, found_job.address_id.name ).encode('cp1252') )
                                    else:
                                        record.append( '' )
                                        record.append( '' )
                                        record.append( compose_fullname( '', found_job.address_id.name ).encode('cp1252') )
                                    record.append( (streetname or '').encode('cp1252') )
                                    record.append( (streetnumber or '').encode('cp1252') )
                                    record.append( (streetbox or '').encode('cp1252') )
                                    record.append( contact.id )
                                    record.append( found_job.id )
                                    record.append( found_job.address_id.id )
                                    if found_job.address_id.partner_id:
                                        record.append( found_job.address_id.partner_id.id )
                                    else:
                                        record.append( 0 )
                                    record.append( 'premium' )
                                    record.append( ( found_job.address_id.magazine_subscription or '' ).encode('cp1252') )
                                    record.append( ( found_job.address_id.magazine_subscription_source or '' ).encode('cp1252') )
                                    record.append( ( found_job.magazine_subscription or '' ).encode('cp1252') )
                                    record.append( ( found_job.magazine_subscription_source or '' ).encode('cp1252') )
                                    record.append( 'C' + str(found_job.id ) )
                                    hfCSV.writerow(record)
                                    #
                                    xmlfile.write(INDENT + '<AddMagazineSubscription StartDate="%s" EndDate="%s">\n' % (in2days.strftime('%Y-%m-%d %H:%M:%S'),cEndDate) )
                                    xmlfile.write(INDENT + INDENT + '<SubscriptionNumber EditionCode="%s">%s</SubscriptionNumber>\n' % ( data['form']['edition_code'],"C"+str(contact.id)) )
                                    xmlfile.write(INDENT + INDENT + '<Subscriber>\n' )
                                    if found_job.address_id.partner_id:
                                        organization_name = compose_fullname( found_job.address_id.partner_id.name, found_job.address_id.name )
                                    else:
                                        organization_name = compose_fullname( '', found_job.address_id.name )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<Organisation>%s</Organisation>\n' % convert_xml( organization_name ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<Salutation>%s</Salutation>\n' % convert_xml( contact.title or '' ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<FirstName>%s</FirstName>\n' % convert_xml( contact.first_name or '' ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<LastName>%s</LastName>\n' % convert_xml( contact.name or '' ) )
                                    xmlfile.write(INDENT + INDENT + '</Subscriber>\n' )
                                    xmlfile.write(INDENT + INDENT + '<Address>\n' )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<StreetName>%s</StreetName>\n' % convert_xml( streetname ) )
                                    if streetnumber:
                                        xmlfile.write(INDENT + INDENT + INDENT + '<HouseNumber>%s</HouseNumber>\n' % convert_xml( streetnumber ) )
                                    if streetbox:
                                        xmlfile.write(INDENT + INDENT + INDENT + '<Box>%s</Box>\n' % convert_xml( streetbox ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<ZipCode>%s</ZipCode>\n' % convert_xml( found_job.address_id.zip_id.name ) )
                                    xmlfile.write(INDENT + INDENT + INDENT + '<MunicipalityName>%s</MunicipalityName>\n' % convert_xml( found_job.address_id.zip_id.old_city or found_job.address_id.zip_id.city ) )
                                    xmlfile.write(INDENT + INDENT + '</Address>\n' )
                                    xmlfile.write(INDENT + INDENT + '<NumberOfPieces>1</NumberOfPieces>\n' )
                                    xmlfile.write(INDENT + '</AddMagazineSubscription>\n' )
                                    #
                                    count_lines += 1
                                    sended_contacts.append( contact.id )
                                    sended_addresses.append( found_job.address_id.id )
                                    

            # end of the xml file
            xmlfile.write('</BePostSubscriptionDistribution>\n')

            data['form']['msg']=_('Save the File with '".xml"' extension.\nThe file has %s lines including %s new subscribers, after dropping %s subscribers. Also temporary %s premium.') % (str(count_lines),str(new_subscriber),str(canceled),str(count_premiums))
            data['form']['postal.xml'] = base64.encodestring(xmlfile.getvalue().encode("utf-8"))
            data['form']['postal.csv'] = base64.encodestring(csvfile.getvalue())
        except StandardError, err:
            data['form']['msg']=_('File NOT created.\n0 lines, 0 prospect...\n\nError :\n%s') % str(err)
        return data['form']

#     states = {
#         'init' : {
#             'actions' : [],
#             'result' : {'type' : 'form',
#                         'arch' : form,
#                         'fields' : form_fields,
#                         'state' : [('end', 'Cancel'),('extract', 'Extract') ],
#             }
#         },
#         'extract' : {
#             'actions' : [_extract_file],
#             'result' : {'type' : 'form',
#                         'arch': msg_form,
#                         'fields' : msg_fields,
#                         'state' : [('end','Close')],
#             },
#         },
#     }
# wizard_get_postal("cci_magazine.get_postal")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

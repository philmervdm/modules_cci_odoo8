# -*- encoding: utf-8 -*-
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
# version 2.0 Philmer : added the VAT number of the partner, and
#                       export to a file rather than sending by mail

from openerp import models, fields, api , _
from openerp import tools
from openerp.exceptions import Warning

import time
import datetime
import re
import base64

def past_month():
    past_month = str(int(time.strftime('%m'))-1)
    if past_month == '0':
        past_month = '12'
    return past_month

def year_past_month():
    past_month_year = int(time.strftime('%Y'))
    if int(time.strftime('%m')) == 1:
        past_month_year = past_month_year - 1
    return past_month_year

MONTHS = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December')
]

msg_form = """<?xml version="1.0"?>
<form string="Notification">
     <separator string="File has been created."  colspan="4"/>
     <field name="msg" colspan="4" nolabel="1"/>
     <field name="file_save" />
</form>"""

msg_fields = {
    'msg': {'string':'File created', 'type':'text', 'size':'100','readonly':True},
    'file_save':{'string': 'Save File',
        'type': 'binary',
        'readonly': True,},
}

def lengthmonth(year, month):
    if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
        return 29
    return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]


class wizard_cert_fed_send(models.TransientModel):
    _name = 'wizard.cert.fed'

    month = fields.Selection(selection=MONTHS,string ='Month',required=True ,default = past_month())
    year = fields.Integer(string = 'Year', size = 4,required= True,default = year_past_month())
    canceled = fields.Boolean(string = 'include canceled certificates',default=True) 
    email_rcp = fields.Char(string = 'Reception email', required = True, help='The e-mail address where receive the proof of receipt (usually yours)')


    _field_separator  = chr(124)
    _record_separator = '\r\n'

    def make_lines(self,res_file):
        lines=[]
        
        # first header line : _field_separator + _record_separator + _field_separator
        # so the receiver can detect which separators we use
        lines.append( self._field_separator + self._record_separator + self._field_separator)
        
        # second header line : give the id code of the CCI, the number of details lines and the email address
        # for the sending of the reception of this file by the federation mail robot
        
        # we obtain the id key of the CCI in the federation
        res_company = self.env['res.company'].browse(1)
        lines.append( res_company.federation_key + self._field_separator + str(len(res_file)).rjust(6,'0') + self._field_separator + str(self.email_rcp).strip() + self._field_separator )
        
        # Let's build a list of certificates objects
        certificates_ids = [x[0] for x in res_file]
        obj_certificate = self.env['cci_missions.certificate']

        # create of list of value, then concatenate them with _field_separator for each certificate
        sequence_num = 0
        total_value = 0
        for cert in certificates_ids:
            fields = []
            sequence_num += 1
            certificate = obj_certificate.browse(cert)
            fields.append( str(sequence_num).rjust(6,'0') )
            fields.append( certificate.digital_number and str(int(certificate.digital_number)) or (certificate.type_id.id_letter + certificate.name.rpartition('/')[0].rpartition('/')[2] + certificate.name.rpartition('/')[2].rjust(6,'0')) )  # extract the right part of the number of the certificate (CO/2008/25 -> '2008' + '25' the left justify with '0' -> '2008000025' )
            fields.append( certificate.dossier_id.asker_name or '')
            fields.append( certificate.asker_address or '')
            fields.append( certificate.asker_zip_id.name or '')
            fields.append( certificate.asker_zip_id.city or '')
            if certificate.order_partner_id.vat and certificate.order_partner_id.vat[0:3].lower() == 'be0':
                fields.append( certificate.order_partner_id.vat[3:12] )
            else:
                fields.append( '000000000' )
            fields.append( certificate.dossier_id.sender_name or '')
            fields.append( certificate.dossier_id.destination_id.code or '')
            fields.append( str( int( certificate.dossier_id.goods_value * 100 )) ) # to have the value in cents, without , or .
            total_value += int( certificate.dossier_id.goods_value * 100 ) # I do this now, because, if I do this just before lines.append, i've got a bug !! If someone has an explanatio, I'm ready
            fields.append( certificate.dossier_id.date.replace('-','') )  # to correct '2008-05-28' to '20080528'
            fields.append( 'Y' )
            custom_codes_string = ''
            for custom_code in certificate.customs_ids:
                custom_codes_string += custom_code.name + self._field_separator
            fields.append( custom_codes_string ) # YES, there will be TWO fields separators at the end of this list, to mark the end of the list, exactly
            origins_string = ''
            for country_code in certificate.origin_ids:
                origins_string += country_code.code + self._field_separator  # country code and not country name
            fields.append( origins_string ) # YES, there will be TWO fields separators at the end of this list, to mark the end of the list, exactly
            lines.append( self._field_separator.join(fields) + self._field_separator )
        
        # Trailer : the sum of all the values in cents of the included certificates
        lines.append( '999999' + self._field_separator + str( total_value ) + self._field_separator )

        # Since we send this file to the federation, we indicate this date in the field  
        # obj_certificate.write(cr, uid,certificates_ids, {'sending_spf' : time.strftime('%Y-%m-%d')})
        return lines

    @api.multi
    def create_file(self):

        # Check of the email address given by the user
        ptrn = re.compile('(\w+@\w+(?:\.\w+)+)')
        result = ptrn.search(self.email_rcp)
        if result==None:
            raise Warning('Error !', 'Enter Valid Reception E-Mail Address.')

        # Determine the first and last date to select
        month = self.month
        year = int(self.year)
        first_day = datetime.date(year,int(month),1)
        last_day = datetime.date(year,int(month),lengthmonth(year, int(month)))
        period = "to_date('" + first_day.strftime('%Y-%m-%d') + "','yyyy-mm-dd') and to_date('" + last_day.strftime('%Y-%m-%d') +"','yyyy-mm-dd')"

        #determine the type of certificates to send
        cancel_clause = not(self.canceled) and " and b.state not in ('cancel_customer','cancel_cci')" or ''
        query = 'select a.id from cci_missions_certificate as a, cci_missions_dossier as b where ( a.dossier_id = b.id ) and ( a.sending_spf is null ) and ( b.date between %s )' + cancel_clause
        #Extraction of corresponding certificates
        self.env.cr.execute(query % (period))
        res_file1 = self.env.cr.fetchall()

        #If no records, cancel of the flow
        if res_file1==[]:
            raise Warning('Notification !', 'No Records Found to be sended. Check your criteria.')

        lines=[]
        root_path = tools.config['root_path']
        
        if res_file1:
            lines=self.make_lines(res_file1)
            result_file = self._record_separator.join(lines).encode('utf-8') + self._record_separator

        msg = 'Save the File with '".txt"' extension.'
        ctx = self.env.context.copy()
        ctx.update({'msg':msg,'file':base64.encodestring(result_file)})
        
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizrad.cert.fed.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

    
class wizard_cert_fed_msg(models.TransientModel):
    _name = 'wizrad.cert.fed.msg'
    
    name = fields.Char('File Name')
    msg = fields.Text(string = 'File created',readonly = True)
    file_save = fields.Binary(string = 'Save File',readonly = True)
    
    @api.model
    def default_get(self, fields):
        res = super(wizard_cert_fed_msg, self).default_get(fields)
        res['name'] = 'fedration.txt'
        res['msg'] = self.env.context.get('msg','')
        res['file_save'] = self.env.context.get('file',False)
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


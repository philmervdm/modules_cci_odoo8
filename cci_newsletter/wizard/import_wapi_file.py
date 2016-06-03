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
# Version 1.0 Philmer

import time
import datetime
import csv
import base64
from openerp import models, fields, api, _
from openerp import tools

class wizard_import_rdp_wapi(models.Model):
    _name = 'wizard.import.rdp.wapi'
    
    source_id = fields.Many2one('cci_newsletter.source', string='Source', required=True)
    input = fields.Binary(string='WAPI CSV file', required=True)
    treatment = fields.Selection([('overwrite', 'Overwrite')], string='Method', required=True)
    explanation = fields.Text(string='Explanation', readonly=True, default=u"You can import a CSV file with 4 and only 4 columns:\n- Sociétés.Nom\n- Contacts.Nom\n- Contacts.Prénom\nContacts.E-mail1\nin that precise order !")
    
    @api.multi
    def import_data(self):
        inputfile = self.input
        inputdata = base64.decodestring(inputfile)
        obj_subscriber = self.env['cci_newsletter.subscriber']
        good_struct = False
        imported = 0
        errors = 0
        deleted = 0
        msg = ''
        if self.treatment == 'overwrite':
            sub_ids = obj_subscriber.search([('source_id', '=', self.source_id.id)])
            sub_ids.unlink()
            deleted = len(sub_ids)
            
            for line in inputdata.splitlines():
                if imported > 0:
                    parts = line.split(";")
                    if len(parts) == 4:
                        (company_name, contact_name, contact_first, email) = parts
                        new_data = {
                            'name': contact_name.decode('cp1252'),
                            'first_name': contact_first.decode('cp1252'),
                            'email': email,
                            'company_name': company_name.decode('cp1252'),
                            'source_id': data['form']['source_id'],
                        }
                        obj_subscriber.create(new_data)
                    else:
                        errors += 1
            else:
                # check if first line is correct
                parts = line.split(";")
                if len(parts) == 4:
                    if parts[0].decode('cp1252') != u'Sociétés.Nom' or parts[1].decode('cp1252') != u'Contacts.Nom' or \
                       parts[2].decode('cp1252') != u'Contacts.Prénom' or parts[3].decode('cp1252') != u'Contacts.E-mail1':
                        good_struct = True
                    else:
                        msg = u"Wrong structure of CSV file : The 4 columns must be named 'Sociétés.Nom', 'Contacts.Nom', 'Contacts.Prénom', 'Contacts.E-mail1' in that order"
                else:
                    msg = u"Wrong structure of CSV file : You must have 4 and only 4 columns"
            imported += 1
        msg = 'Number of imported subscribers : %s\nDeleted : %s\nErrors (probably ; in names) : %s' % (str(imported - 1), str(deleted), str(errors))
        
        ctx = self.env.context.copy()
        # give the result tos the user
        ctx.update({'msg': msg, 'data': base64.encodestring(inputdata)})
        
        view = self.env.ref('cci_newsletter.view_wizard_import_rdp_wapi_msg_form')
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.rdp.wapi.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }


class wizard_import_rdp_wapi_msg(models.Model):
    _name = 'wizard.import.rdp.wapi.msg'
    
    msg = fields.Text(string='File imported', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(wizard_import_rdp_wapi_msg, self).default_get(fields)
        if self.env.context.get('data'):
            rec['subscribers_xls'] = self.env.context['data']
        if self.env.context.get('msg'):
            rec['msg'] = self.env.context['msg']
        return rec
   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
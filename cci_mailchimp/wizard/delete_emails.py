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
from openerp import models, fields, api, _

class cci_delete_emails_in_tables(models.TransientModel):
    _name = 'cci.delete.emails.in_tables'
    
    emails = fields.Text('email(s) to delete', help='List of emails separated by a <enter>')
    send_warning = fields.Boolean('Send Warning to Data Sources', help='Send a warning of \'other chambers\' responsibles if corrections in newsletter subscribers')
    
    @api.multi
    def delete(self):
        if self.emails:
            list_to_delete = self.emails.split('\n')
            list_to_delete = [x.strip() for x in list_to_delete if len(x.strip()) > 0]
            obj_mailchimp_proxy = self.env['mailchimp_proxy']
            final_count = obj_mailchimp_proxy.delete_email(list_to_delete, self.send_warning)
        else:
            final_count = 0
            
        ctx = self.env.context.copy()
        ctx.update({'final_count': final_count})
        view = self.env.ref('cci_mailchimp.view_cci_delete_emails_in_tables_count')
        
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.delete.emails.in_tables.count',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_delete_emails_in_tables_count(models.TransientModel):
    _name = 'cci.delete.emails.in_tables.count'
    
    final_count = fields.Integer('Deletions Count', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_delete_emails_in_tables_count, self).default_get(fields)
        if self.env.context.get('final_count'):
            rec['final_count'] = self.env.context['final_count']
        return rec
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
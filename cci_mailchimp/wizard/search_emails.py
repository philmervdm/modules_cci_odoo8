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
# This wizard searchs for emails addresses in a list of given table

import time
import datetime
from openerp import models, fields, api, _

class cci_mailchimp_search_emails(models.TransientModel):
    _name = 'cci.mailchimp.search.emails'
    
    email = fields.Char(string='email or part of email address', help='You can search on part of emails : like \'@cci.\', for example')
    
    @api.multi
    def search(self):
        usage_ids = []
        if self.email:
            parameter_obj = self.env['ir.config_parameter']
            param_values = parameter_obj.get_param(['MailTables'])
            if param_values.has_key('MailTables'):
                tables = param_values['MailTables']
            else:
                tables = [('res.partner', 'email')]
            obj_usage = self.env['mail_usage']
            for (table_name, field_name) in tables:
                current_obj = self.env[table_name]
                current_ids = current_obj.search([(field_name, 'ilike', self.email)])
                if current_ids:
                    current_values = current_obj.read(['id', field_name])
                    for current_usage in current_values:
                        new_id = obj_usage.create({ 
                            'name':current_usage[field_name],
                            'source':table_name,
                            'source_id':int(current_usage['id']),
                        })
                        usage_ids.append(int(new_id.id))
        value = {
            'domain': [('id', 'in', usage_ids)],
            'name': _('Mail Usage'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mail_usage',
            'context': {},
            'type': 'ir.actions.act_window',
            }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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

import datetime
from openerp import models, fields, api, _ 

class cci_correct_emails_in_tables(models.TransientModel):
    _name = 'cci.correct.email.is_tables'
    
    from_correct = fields.Char('Correct', required=True)
    to_correct = fields.Char('To', required=True)
    
    @api.multi
    def correct_data(self):
        from_string = self.from_correct.decode('utf-8')
        to_string = self.from_correct.decode('utf-8')
        if self.env.context['active_ids'] and from_string and to_string and from_string != to_string:
            final_count = 0
            obj_usage = self.env['mail_usage']
            usage = obj_usage.browse(self.env.context['active_ids'])
            usages = usage.read(['id', 'name', 'source', 'source_id'])
            parameter_obj = self.env['ir.config_parameter']
            param_values = parameter_obj.get_param(['MailTables'])
            if param_values.has_key('MailTables'):
                def_tables = param_values['MailTables']
            else:
                def_tables = [('res.partner', 'email')]
            dTableField = {}
            for table in def_tables:
                dTableField[table[0]] = table[1]
            tables = []
            for usage in usages:
                if usage['source'] not in tables:
                    tables.append(usage['source'])
            if tables:
                for table_name in tables:
                    if dTableField.has_key(table_name):
                        field_name = dTableField[table_name]
                        current_obj = pooler.get_pool(cr.dbname).get(table_name)
                        for usage in usages:
                            if usage['source'] == table_name:
                                old_email = usage['name']
                                new_email = old_email.replace(from_string, to_string)
                                if old_email != new_email:
                                    current_obj.write(cr, uid, [usage['source_id']], {field_name:new_email})
                                    final_count += 1
            final_count = final_count
        else:
            final_count = 0
        # give the result to the user
        ctx = self.env.context.copy()
        ctx.update({'final_count': final_count})
        view = self.env.ref('cci_mailchimp.view_cci_correct_emails_in_tables_count')
        
        return {
            'name': _('Results'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.correct.email.is_tables.count',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_correct_emails_in_tables_count(models.TransientModel):
    _name = 'cci.correct.email.is_tables.count'
    
    final_count = fields.Integer('Corrections Count', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_correct_emails_in_tables_count, self).default_get(fields)
        if self.env.context.get('final_count'):
            rec['final_count'] = self.env.context['final_count']
        return rec
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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
from openerp import api, fields, models, _
import base64
from xlwt import *


class extract_membership_by_year(models.TransientModel):
    _name = 'extract.membership_by_year'

    choice = fields.Selection([('all', 'Toutes les fiches préparées'),
                               ('selected', 'Seulement les sélectionnées')],
                              string='Selection', required=True, default='all')

    @api.multi
    def get_file(self):
        record_obj = self.env['cci_membership.membership_by_partner']
        record_ids = self.env.context.get('active_ids')
        fields = ['partner_id', 'partner_name', 'user_id', 'user_name', 'year', 'invoiced', 'paid', 'canceled', 'open']
        records = record_obj.browse(record_ids)
        wb = Workbook()
        ws1 = wb.add_sheet('Membership by Year and Partner')
        for index in range(0, len(fields)):
            ws1.write(0, index, fields[index])
        line = 1
        for record in records:
            ws1.write(line, 0, record.id)
            ws1.write(line, 1, record.name)
            ws1.write(line, 2, record.user_id and record.user_id.id or "")
            ws1.write(line, 3, record.user_id and record.user_id.name or "")
            ws1.write(line, 4, record.year)
            ws1.write(line, 5, record.invoiced)
            ws1.write(line, 6, record.paid)
            ws1.write(line, 7, record.canceled)
            ws1.write(line, 8, record.open)
            line += 1
        wb.save('membership_by_year.xls')
        result_file = open('membership_by_year.xls', 'rb').read()

        # give the result tos the user
        view = self.env.ref('cci_membership_extend.view_wizard_extract_membership_by_year_msg_form')
        ctx = self.env.context.copy()
        ctx['msg'] = 'Save the File with '".xls"' extension.'
        ctx['file'] = base64.encodestring(result_file)
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.membership_by_year.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx
        }


class wizard_extract_membership_by_year_msg(models.TransientModel):
    _name = 'wizard.extract.membership_by_year.msg'

    name = fields.Char(string='File name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    membership_by_year_xls = fields.Binary(string='Prepared file', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_extract_membership_by_year_msg, self).default_get(fields)
        res['name'] = 'membership_by_year.xls'
        res['msg'] = self.env.context.get('msg')
        res['membership_by_year_xls'] = self.env.context.get('file')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

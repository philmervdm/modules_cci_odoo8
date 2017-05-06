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
from xlwt import *
import base64


class extract_calls_in_excel(models.TransientModel):
    _name = 'extract.calls_in_excel'

    choice = fields.Selection([('all', 'Tous les appels préparés'),
                               ('selected', 'Seulement les sélectionnés')],
                              required=True, default='all', string='Selection')

    @api.multi
    def get_file(self):
        call_obj = self.env['cci_membership.membership_call']
        if self.choice == 'all':
            call_ids = call_obj.search([])
        else:
            call_ids = call_obj.browse(self.env.context.get('active_ids'))
        fields = ['partner_id', 'address_id', 'job_id', 'contact_id', 'partner_name',
                  'street', 'street2', 'zip_code', 'city', 'email_addr', 'phone_addr', 'fax_addr',
                  'name', 'first_name', 'courtesy', 'title', 'title_categs', 'email_contact',
                  'base_amount', 'count_add_sites', 'unit_price_site', 'desc_add_site', 'wovat_amount', 'wvat_amount',
                  'salesman', 'salesman_phone', 'salesman_fax', 'salesman_mobile', 'salesman_email', 'vcs']
        if call_ids:
            calls = call_ids.read(fields)
        else:
            calls = []
        # get the data about all contact title
        title_obj = self.env['res.partner.title']
        title_ids = title_obj.search([('domain', '=', 'contact')])
        titles = title_ids.read(['id', 'shortcut', 'name', 'other1', 'other2'])
        dTitles = {}
        for tit in titles:
            dTitles[tit['shortcut']] = tit
        #
        wb1 = Workbook()
        ws1 = wb1.add_sheet('Appels')
        for index in range(0, len(fields)):
            ws1.write(0, index, fields[index])
        index += 1
        ws1.write(0, index, 'courtesy1')
        index += 1
        ws1.write(0, index, 'courtesy2')
        line = 1
        for call in calls:
            for index in range(0, len(fields)):
                if fields[index] in ['partner_id', 'address_id', 'job_id', 'contact_id']:
                    ws1.write(line, index, call[fields[index]] and call[fields[index]][0] or 0)
                else:
                    ws1.write(line, index, call[fields[index]] or '')
            courtesy1 = ''
            courtesy2 = ''
            if call['courtesy'] and dTitles.has_key(call['courtesy']):
                courtesy1 = dTitles[call['courtesy']]['other1'] or ''
                courtesy2 = dTitles[call['courtesy']]['other2'] or ''
            index += 1
            ws1.write(line, index, courtesy1)
            index += 1
            ws1.write(line, index, courtesy2)
            line += 1
        wb1.save('calls.xls')
        result_file = open('calls.xls', 'rb').read()

        # give the result tos the user

        view = self.env.ref('cci_membership_extend.view_wizard_extract_calls_2_excel_msg_form')
        ctx = self.env.context.copy()
        ctx['msg'] = 'Save the File with '".xls"' extension.'
        ctx['file'] = base64.encodestring(result_file)
        return {
            'name': _('Result'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.calls_2_excel.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx
        }


class wizard_extract_calls_2_excel_msg(models.TransientModel):
    _name = 'wizard.extract.calls_2_excel.msg'

    name = fields.Char(string='File name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    calls_xls = fields.Binary(string='Prepared file', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_extract_calls_2_excel_msg, self).default_get(fields)
        res['name'] = 'calls.xls'
        res['msg'] = self.env.context.get('msg')
        res['calls_xls'] = self.env.context.get('file')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

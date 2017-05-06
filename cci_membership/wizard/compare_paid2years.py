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
from openerp import api, fields, models, _
from openerp.exceptions import Warning
import datetime
import base64
from xlwt import *


class compare_paid2years(models.TransientModel):
    _name = 'compare.paid2years'

    year = fields.Integer(string='Last year',
                          help='Last of the two years; the first will be calculed from the last ... difficult ...',
                          required=True, default=datetime.datetime.today().year - 1)

    @api.multi
    def create_excel_file(self):
        # manage parameters
        if not self.year:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.year and self.year < 1900:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        # we extract the 'membership products' for the tw concerned years
        # for theses products, we extract all account.invoice.line.
        # For each invoice.line we check if invoice type is sale and if the move linked to the invoice is reconciled on 'receivable' account
        # We keep the id and the amount for each such invoice.line and the concerned years
        # with the invoice_lines ids, we extract concerned partners
        # and for each concerned partners we cumulate by years and compare the two years in excel file
        # we do this because the 'paid' state of invoices is not trustable at 100%
        year1 = self.year-1
        year2 = self.year
        concerned_years = [year1, year2]
        product_obj = self.env['product.product']
        product_ids = product_obj.search([('membership', '=', True),
                                          ('membership_year', 'in', concerned_years),
                                          '|', ('active', '=', True), ('active', '=', False)])
        if not product_ids:
            raise Warning(_('Warning'),
                          _('There is no membership products for the concerned years : %s and %s' % (concerned_years[0],
                                                                                                     concerned_years[1])))
        products = product_ids.read(['id', 'membership_year'])
        dProducts = {}
        for prod in products:
            dProducts[prod['id']] = prod['membership_year']
        ailine_obj = self.env['account.invoice.line']
        ailines = ailine_obj.search([('product_id', 'in', product_ids.ids)])
        if not ailines:
            raise Warning(_('Warning'),
                          _('There is no invoices for the concerned years : %s and %s' % (concerned_years[0],
                                                                                          concerned_years[1])))
        account_obj = self.env['account.account']
        receivable_account_ids = account_obj.search([('type', '=', 'receivable')])
        concerned_ailine_ids = []
        dAILines = {}
        for ailine in ailines:
            move_reconciled = False
            if ailine.invoice_id and ailine.invoice_id.state in ('open', 'paid') and ailine.invoice_id.journal_id and ailine.invoice_id.journal_id.type == 'sale':
                if ailine.invoice_id.move_id and ailine.invoice_id.move_id.line_id:
                    for mline in ailine.invoice_id.move_id.line_id:
                        if mline.account_id.id in receivable_account_ids.ids and mline.reconcile_id:
                            move_reconciled = True
            if move_reconciled:
                concerned_ailine_ids.append(ailine.id)
                dAILines[ailine.id] = {'amount': ailine.price_subtotal, 'year': dProducts[ailine.product_id.id]}
        mmline_obj = self.env['membership.membership_line']
        mmlines = mmline_obj.search([('account_invoice_line', 'in', concerned_ailine_ids)])
        dPartners = {}
        for mmline in mmlines:
            if mmline.partner:
                if dPartners.has_key(mmline.partner.id):
                    partner = dPartners[mmline.partner.id]
                else:
                    partner = {'name': mmline.partner.name, 'year1':0.0, 'year2':0.0}
                if dAILines[mmline.account_invoice_line.id]['year'] == year1:
                    partner['year1'] += dAILines[mmline.account_invoice_line.id]['amount']
                else:
                    partner['year2'] += dAILines[mmline.account_invoice_line.id]['amount']
                dPartners[mmline.partner.id] = partner
        wb = Workbook()
        ws1 = wb.add_sheet('Partners')
        ws1.write(0, 0, u'partner_id')
        ws1.write(0, 1, u'name')
        ws1.write(0, 2, u'Paid %s' % str(year1))
        ws1.write(0, 3, u'Paid %s' % str(year2))
        ws1.write(0, 4, u'Status')
        ws1.write(0, 5, u'Amount Diff')
        line = 1
        count_lost = 0
        count_new = 0
        count_less = 0
        count_more = 0
        count_year1 = 0
        count_year2 = 0
        count_year1_faithfull = 0
        amount_year1 = 0.0
        amount_year2 = 0.0
        for (partner_id, partner) in dPartners.items():
            ws1.write(line, 0, partner_id)
            ws1.write(line, 1, partner['name'])
            ws1.write(line, 2, partner['year1'])
            ws1.write(line, 3, partner['year2'])
            if partner['year1'] >= 0.001 and partner['year2'] <= 0.001:
                ws1.write(line, 4, 'lost')
                count_lost += 1
            elif partner['year1'] <= 0.001 and partner['year2'] >= 0.001:
                ws1.write(line, 4, 'new')
                count_new += 1
            elif partner['year1'] >= 0.001 and partner['year2'] >= 0.001 and partner['year1'] > partner['year2']:
                ws1.write(line, 4, 'less money')
                count_less += 1
            elif partner['year1'] >= 0.001 and partner['year2'] >= 0.001 and partner['year1'] < partner['year2']:
                ws1.write(line, 4, 'more money')
                count_more += 1
            if partner['year1'] >= 0.001:
                count_year1 += 1
            if partner['year2'] >= 0.001:
                count_year2 += 1
            amount_year1 += partner['year1']
            amount_year2 += partner['year2']
            if partner['year1'] >= 0.001 and partner['year2'] >= 0.001:
                count_year1_faithfull += 1
            ws1.write(line, 5, partner['year2']-partner['year1'])
            line += 1
        # record the global data on worsheet 2
        ws2 = wb.add_sheet('Global Data')
        ws2.write(0, 0, 'Global Results')
        ws2.write(1, 0, 'Date')
        ws2.write(1, 1, datetime.datetime.today().strftime('%d/%m/%Y'))
        ws2.write(2, 0, 'Lost')
        ws2.write(2, 1, count_lost)
        ws2.write(3, 0, 'New')
        ws2.write(3, 1, count_new)
        ws2.write(4, 0, 'Less money')
        ws2.write(4, 1, count_less)
        ws2.write(5, 0, 'More money')
        ws2.write(5, 1, count_more)
        ws2.write(6, 0, 'Count Year1')
        ws2.write(6, 1, count_year1)
        ws2.write(7, 0, 'Count Year2')
        ws2.write(7, 1, count_year2)
        ws2.write(8, 0, 'Year1 faithfull')
        ws2.write(8, 1, count_year1_faithfull)
        ws2.write(9, 0, 'Fidelity Rate')
        if count_year1:
            ws2.write(9, 1, int(count_year1_faithfull*100/count_year1))
        else:
            ws2.write(9, 1, 0)
        ws2.write(10, 0, 'Amount Year 1')
        ws2.write(10, 1, amount_year1)
        ws2.write(11, 0, 'Amount Year 2')
        ws2.write(11, 1, amount_year2)
        wb.save('compare2paidmembers.xls')
        result_file = open('compare2paidmembers.xls', 'rb').read()

        # give the result tos the user
        view = self.env.ref('cci_membership_extend.view_wizard_compare_paid2years_msg_form')
        ctx = self.env.context.copy()
        ctx['msg'] = 'Save the File with '".xls"' extension.'
        ctx['file'] = base64.encodestring(result_file)
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.compare.paid2years.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx
        }


class wizard_compare_paid2years_msg(models.TransientModel):
    _name = 'wizard.compare.paid2years.msg'

    name = fields.Char(string='File name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    compare2paidmembers_xls = fields.Binary(string='Prepared file', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_compare_paid2years_msg, self).default_get(fields)
        res['name'] = 'compare2paidmembers.xls'
        res['msg'] = self.env.context.get('msg')
        res['compare2paidmembers_xls'] = self.env.context.get('file')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

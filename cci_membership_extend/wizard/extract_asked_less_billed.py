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


class extract_asked_less_billed(models.TransientModel):

    _name = 'extract.asked.less.billed'

    only_members = fields.Boolean(string='Only for current members', default=True,
                                  help='If not checked, the list will give ALL partners billed once in the last years \
                                  with a next membership lower than the last invoiced...')

    @api.multi
    def open_window_selected_partners(self):
        # search all membership products ids
        mprods = self.env['product.product'].search([('membership', '=', True)])
        # get the id of the journal of invoices
        journal_id = self.env['account.journal'].search([('code', '=', 'VEN')], limit=1)
        # get the value of all membership invoices ordered by partner and date descending
        last_invoice_selection = "SELECT SUM(credit-debit) as amount, MAX(partner_id) as partner_id, MAX(date) as date \
        FROM account_move_line where journal_id = %s \
        AND product_id in (%s) \
        GROUP BY move_id ORDER BY partner_id, date DESC" % (str(journal_id.ids), ','.join([str(x) for x in mprods.ids]))
        self.env.cr.execute(last_invoice_selection)
        invoices = self.env.cr.fetchall()
        dLastInvoice = {}
        partner_ids = []
        for invoice in invoices:
            if not dLastInvoice.has_key(int(invoice[1])):  # we record only the first (and thus the last one in term of date) by partner
                dLastInvoice[int(invoice[1])] = float(invoice[0])
                partner_ids.append(int(invoice[1]))
        if self.only_members:
            selection = "SELECT id, membership_amount FROM res_partner \
            WHERE active \
            AND membership_state in ('free','invoiced','paid') \
            AND state_id = 1"
        else:
            selection = "SELECT id, membership_amount FROM res_partner \
            WHERE active AND state_id = 1 \
            AND id in (%s)" % (','.join([str(x) for x in partner_ids]))
        self.env.cr.execute(selection)
        partners = self.env.cr.fetchall()
        partner_ids = []
        for partner in partners:
            if dLastInvoice.has_key(int(partner[0])):
                if float(partner[1]) < float(dLastInvoice[partner[0]]) and float(partner[1]) > 0.0:
                    partner_ids.append(int(partner[0]))
        result = {
            'domain': [('id', 'in', partner_ids)],
            'name': _('Partners with lower membership than last invoiced'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

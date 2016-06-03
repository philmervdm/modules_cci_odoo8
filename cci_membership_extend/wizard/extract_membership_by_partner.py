# -*- coding: utf-8 -*-
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


class extract_membership_by_partner(models.TransientModel):
    _name = 'extract.membership.by_partner'

    year = fields.Integer(string='Membership year')

    @api.multi
    def extract_totals_by_partner(self):
        # manage parameters
        year = self.year
        # get the products linked to the membership (and the possible year)
        prod_obj = self.env['product.product']
        if year:
            prod_ids = prod_obj.search([('membership', '=', True), ('membership_year', '=', year)])
        else:
            prod_ids = prod_obj.search([('membership', '=', True)])
        if prod_ids:
            # get the list of sales journals and refund_sales journals
            jnl_obj = self.env['account.journal']
            NCV_ids = jnl_obj.search([('type', '=', 'sale_refund')])
            VEN_ids = jnl_obj.search([('type', '=', 'sale')])
            # get the list of 'customer accounts'
            account_types = self.env['account.account.type'].search([('code', '=', 'tiers -rec')])
            accounts = self.env['account.account'].search([('user_type', 'in', account_types.ids)])
            # extract all lines concerned by these products
            iline_obj = self.env['account.move.line']
            ilines = iline_obj.search([('product_id', 'in', prod_ids.ids)])
            dYearPartners = {}
            for iline in ilines:
                key = (iline.product_id.membership_year or 1900, iline.partner_id.id or 0)
                if not dYearPartners.has_key(key):
                    newrecord = {'partner_id': iline.partner_id.id or 0,
                                 'user_id': iline.partner_id.user_id.id or 0,
                                 'year': iline.product_id.membership_year or 1900,
                                 'invoiced': 0.0,
                                 'paid': 0.0,
                                 'canceled': 0.0,
                                 'open': 0.0}
                    dYearPartners[key] = newrecord
                if iline.journal_id.id in VEN_ids.ids:
                    dYearPartners[key]['invoiced'] += (iline.credit - iline.debit)
                    # for the sales lines, we must check if paid by another line than sales_refund
                    lPaid = False
                    lRefund = False
                    if iline.move_id and iline.move_id.line_id:
                        for assoc_line in iline.move_id.line_id:
                            if assoc_line.account_id.id in accounts.ids and assoc_line.reconcile_id.id:
                                # check the journal of the lines linked to this one : if there is a refund, consider the invoice as refunded
                                for other_line in assoc_line.reconcile_id.line_id:
                                    lPaid = True
                                    if other_line.id != iline.id:
                                        if other_line.journal_id.id in NCV_ids.ids:
                                            lRefund = True
                    if lPaid:
                        if not lRefund:
                            dYearPartners[key]['paid'] += (iline.credit - iline.debit)
                        else:
                            dYearPartners[key]['canceled'] += (iline.credit - iline.debit)
                    else:
                        dYearPartners[key]['open'] += (iline.credit - iline.debit)
                elif iline.journal_id.id in NCV_ids.ids:
                    # dYearPartners[ key ]['canceled'] += ( iline.debit - iline.credit )
                    pass
                else:
                    print iline.journal_id.id
            # record in the database to show it to the user
            record_obj = self.env['cci_membership.membership_by_partner']
            list_ids = []
            for data in dYearPartners.values():
                list_ids.append(record_obj.create({'partner_id': data['partner_id'],
                                                   'user_id': data['user_id'],
                                                   'year': data['year'],
                                                   'invoiced': data['invoiced'],
                                                   'paid': data['paid'],
                                                   'canceled': data['canceled'],
                                                   'open': data['open']}).id)
        else:
            raise Warning(_('Warning'),
                          _("There is no membership products associated with the year '%s' !" % str(year)))
            list_ids = []
        value = {
                'domain': [('id', 'in', list_ids)],
                'name': _('Total membership(s) by Partner by year'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'cci_membership.membership_by_partner',
                'type': 'ir.actions.act_window',
                'limit': len(list_ids),
            }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

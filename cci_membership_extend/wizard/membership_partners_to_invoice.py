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
# This wizard select all partners invoiced with a specificed product last year
import datetime
from openerp import api, fields, models, _
from openerp.exceptions import Warning


class membership_partners_to_invoice(models.TransientModel):
    _name = 'membership.partners_to_invoice'

    year = fields.Integer(string='New year', help='New year of the called membership...',
                          required=True, default=datetime.datetime.today().year + 1)
    also_invoiced = fields.Boolean(string='Also the invoiced members, else only paid')
    also_forced = fields.Boolean(string='Also the forced partners', default=True)
    old_product_id = fields.Many2one('product.product', string='Old Product to Search',
                                     domain="[('membership','=',True)]", required=True)

    @api.multi
    def open_window_results(self):
        # manage parameters
        if not self.year:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.year and self.year < 1900:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.also_invoiced:
            mstates = ['invoiced', 'paid']
            smstates = "('invoiced', 'paid')"
        else:
            mstates = ['paid']
            smstates = "('paid')"
        # get this list of partners already invoiced for the next year of membership
        # on basis of membership products for this year, active or not
        mprod_obj = self.env['product.product']
        mprod_ids = mprod_obj.search([('membership', '=', True),
                                      ('membership_year', '=', self.year),
                                      '|', ('active', '=', True), ('active', '=', False)])
        excluded_partner_ids = []
        if len(mprod_ids) > 0:
            selection = "SELECT distinct(partner_id) \
                        FROM account_move_line \
                        where product_id in (%s)" % ','.join([str(x) for x in mprod_ids.ids])
            self.env.cr.execute(selection)
            partners = self.env.cr.fetchall()
            excluded_partner_ids = [x[0] for x in partners]
        # get all partners to be invoiced
        selection = "SELECT id FROM res_partner \
                    where active AND state_id = 1 \
                    AND membership_state in %s \
                    AND membership_amount > 0.1 \
                    AND id in (SELECT distinct(partner_id) FROM account_move_line where product_id = %s) \
                    AND NOT refuse_membership \
                    AND NOT free_member \
                    AND associate_member IS NULL" % (smstates, self.old_product_id.id)
        self.env.cr.execute(selection)
        partners = self.env.cr.fetchall()
        partner_ids = [x[0] for x in partners if x[0] not in excluded_partner_ids]
        if self.also_forced:
            forced_partner_ids = self.env['res.partner'].search([('state_id', '=', 1),
                                                                 ('membership_amount', '>', 0.1),
                                                                 ('next_membership_bill_forced', '=', True)])
            for partner_id in forced_partner_ids.ids:
                if partner_id not in partner_ids:
                    partner_ids.append(partner_id)
        result = {
            'name': _('Partners to Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', partner_ids)],
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

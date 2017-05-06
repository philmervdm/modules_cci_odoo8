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
import datetime


class use_membership_products(models.TransientModel):
    _name = 'use.membership.products'

    from_year = fields.Integer(string='From (membership year)',
                               default=int(datetime.datetime.today().strftime('%Y')), required=True)
    to_year = fields.Integer(string='To (membership year)', default=datetime.datetime.today().strftime('%Y'),
                             required=True)

    @api.multi
    def search_products(self):
        from_year = min(self.from_year, self.to_year)
        to_year = max(self.from_year, self.to_year)

        selection = "SELECT id from product_template \
                        where membership_year BETWEEN %s AND %s" % (str(from_year), str(to_year))
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        if len(res) == 0:
            prod_ids = ''
        else:
            prod_ids = (','.join([str(x[0]) for x in res])) + ','
        result = {
            'name': _("Products used for membership's bills between %s and %s") % (from_year, to_year),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            'domain': "[('id', 'in', [%s]), '|', ('active', '=', True), ('active', '=', False)]" % prod_ids,
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

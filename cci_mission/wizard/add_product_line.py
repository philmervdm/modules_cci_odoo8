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
from openerp import models, fields, api , _

class add_product_line(models.TransientModel):
    _name = 'wizard.add.product.line'
    
    product_id = fields.Many2one('product.product',string = 'Product', required = True)
    
    @api.multi
    def createlines(self):
        sale_taxes = []
        product =  self.product_id
        if product.taxes_id:
            map(lambda x: sale_taxes.append(x.id), product.taxes_id)
        a =  product.product_tmpl_id.property_account_income.id or False
        if not a:
            a = product.categ_id.property_account_income_categ.id
        value = {
             'product_id': product.id or False,
             'name': product.name,
             'quantity': 1,
             'uos_id': product.uom_id.id or False,
             'price_unit': product.list_price or 0.0,
             'dossier_product_line_id': self.env.context.get('active_id'),
             'taxes_id': [(6, 0, sale_taxes)],
             'account_id':a
                 }
        id = self.env['product.lines'].create(value)
        return {}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
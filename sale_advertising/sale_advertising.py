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

from openerp import models, fields, api
import time

class sale_order(models.Model):
    _inherit = "sale.order"

    published_customer = fields.Many2one('res.partner','Published Customer')
    advertising_agency = fields.Many2one('res.partner','Advertising Agency')

    @api.multi
    def onchange_published_customer(self, published_customer):
        data = {'advertising_agency':published_customer,'partner_id':published_customer,'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}
        if published_customer:
            address = self.onchange_partner_id(published_customer)
            data.update(address['value'])
        return {'value' : data}
    
    @api.multi
    def onchange_advertising_agency(self, ad_agency):
        data = {'partner_id':ad_agency,'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}
        if ad_agency:
            address = self.onchange_partner_id(ad_agency)
            data.update(address['value'])
        return {'value' : data}

class sale_advertising_issue(models.Model):
    _name = "sale.advertising.issue"
    _description="Sale Advertising Issue"
    
    name = fields.Char('Name', size=32, required=True)
    issue_date = fields.Date('Issue Date', required=True, default=time.strftime('%Y-%m-%d'))
    medium = fields.Many2one('product.category','Medium', required=True)
    state = fields.Selection([('open','Open'),('close','Close')], 'State', default='open')
    default_note = fields.Text('Default Note')

class sale_order_line(models.Model):
    _inherit = "sale.order.line"
    
    layout_remark = fields.Text('Layout Remark')
    adv_issue = fields.Many2one('sale.advertising.issue','Advertising Issue')
    page_reference = fields.Char('Reference of the Page', size=32)
    from_date = fields.Datetime('Start of Validity', help='You can use this field if you are selling advertising limited in time, like banners on a website')
    to_date = fields.Datetime('End of Validity', help='You can use this field if you are selling advertising limited in time, like banners on a website')
    user_id = fields.Many2one(related='order_id.user_id', string='Salesman', relation='res.users', required=True)

class product_product(models.Model):
    _inherit = "product.product"
    
    equivalency_in_A4 = fields.Float('A4 Equivalency',digits=(16,2))

class sale_advertising_proof(models.Model):
    _name = "sale.advertising.proof"
    _description="Sale Advertising Proof"
    
    name = fields.Char('Name', size=32, required=True)
    address_id = fields.Many2one('res.partner','Delivery Address', required=True)
    number = fields.Integer('Number of Copies', required=True, default=1)
    target_id = fields.Many2one('sale.order','Target', required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


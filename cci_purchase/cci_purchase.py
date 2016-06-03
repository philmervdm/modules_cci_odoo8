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


import time
from openerp import models, fields, api, _
from openerp import workflow
from openerp.exceptions import Warning


class purchase_order_history(models.Model):
    _name = 'purchase.order.history'
    _decription = 'purchase order'
    _rec_name = 'date'

    purchase_id = fields.Many2one('purchase.order', string='PO Ref')
    date = fields.Date(string='Modification Date')
    user_id = fields.Many2one('res.users', string='User')

class purchase_order(models.Model):
    _inherit = 'purchase.order'
    _decription = 'purchase order'

    history_ids = fields.One2many('purchase.order.history','purchase_id', string='PO Ref')
    internal_notes = fields.Text(string='Internal Note')
    approvator = fields.Many2one('res.users', string='Approved by', readonly=True)
    state = fields.Selection([('draft', 'Draft PO'), ('sent', 'RFQ'), ('bid', 'Bid Received'), ('confirmed', 'Waiting Approval'), ('wait_approve','Waiting For Approve'), ('approved', 'Purchase Confirmed'), ('except_picking', 'Shipping Exception'), ('except_invoice', 'Invoice Exception'), ('done', 'Done'), ('cancel', 'Cancelled')], string='Order State', readonly=True, help="The state of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' state. Then the order has to be confirmed by the user, the state switch to 'Confirmed'. Then the supplier must confirm the order to change the state to 'Approved'. When the purchase order is paid and received, the state becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the state becomes in exception.", select=True)

    @api.multi
    def wkf_temp_order0(self):
        self.write({'state': 'wait_approve'})
        return True

    @api.multi
    def button_purchase_temp(self):
        for po in self:
            if po.amount_total < 10000:
                workflow.trg_validate(self._uid, 'purchase.order', po.id, 'purchase_confirm', self._cr)
            else:
                workflow.trg_validate(self._uid, 'purchase.order', po.id, 'purchase_tempo', self._cr)
        return True

    @api.multi
    def action_invoice_create(self):
        res = False
        journal_obj = self.env['account.journal']
        fiscal_pool = self.env['account.fiscal.position']
        inv_line_obj= self.env['account.invoice.line']
        for o in self:
            il = []
            for ol in o.order_line:
                if ol.product_id:
                    a = ol.product_id.product_tmpl_id.property_account_expense.id
                    if not a:
                        a = ol.product_id.categ_id.property_account_expense_categ.id
                    if not a:
                        raise Warning(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (ol.product_id.name, ol.product_id.id,))
                else:
                    a = self.env['ir.property'].get('property_account_expense_categ', 'product.category')
                fpos = o.fiscal_position
                a = fpos.map_account(a)
                inv_line_data = self._prepare_inv_line(a, ol)
                inv_line_id = inv_line_obj.create(inv_line_data)
                il.append(inv_line_id.id)
                ol.write({'invoice_lines': [(4, inv_line_id.id)]})

            a = o.partner_id.property_account_payable.id
            # journal_ids = journal_obj.search([('type', '=','purchase')], limit=1)
            journal_ids = journal_obj.search([('type', '=', 'purchase'), ('company_id', '=', o.company_id.id)], limit=1)
            if not journal_ids:
                raise Warning(
                    _('Error!'),
                    _('Define purchase journal for this company: "%s" (id:%d).') % \
                        (o.company_id.name, o.company_id.id))
            inv = {
                'name': o.partner_ref or o.name,
                'reference': "P%dPO%d" % (o.partner_id.id, o.id),
                'account_id': a,
                'type': 'in_invoice',
                'partner_id': o.partner_id.id,
                'currency_id': o.pricelist_id and o.pricelist_id.currency_id and o.pricelist_id.currency_id.id,
                # 'address_invoice_id': o.partner_address_id.id,
                # 'address_contact_id': o.partner_address_id.id,
                'journal_id': journal_ids and journal_ids[0].id or False,
                'origin': o.name,
                'invoice_line': [(6, 0, il)],
                'fiscal_position': o.partner_id.property_account_position.id,
                'payment_term':o.partner_id.property_payment_term and o.partner_id.property_payment_term.id or False,
                # 'internal_note': o.internal_notes,
            }
            inv_id = self.env['account.invoice'].create(inv, context={'type':'in_invoice','from_purchase':True})
            inv_id.button_compute(set_total=True)
#            self.pool.get('account.invoice').button_compute(self._cr, self._uid, [inv_id.id], context={'type':'in_invoice'}, set_total=True)
 #           self.pool.get('account.invoice').button_compute(self._cr, self._uid, [inv_id.id], context={'type':'in_invoice'}, set_total=True)
            o.write({'invoice_ids': [(4, inv_id.id)]})
            # res = inv_id
            res = inv_id.id
        return res

    @api.multi
    def write(self, vals):
        result = super(purchase_order, self).write(vals)
        return result
#    def wkf_write_approvator(self, cr, uid, ids, context={}):
#        wf_service = netsvc.LocalService('workflow')
#        for po in self.browse(cr, uid, ids):
#            self.write(cr, uid, [po.id], { 'validator' : uid})
#            wf_service.trg_validate(uid, 'purchase.order', po.id, 'purchase_dummy_confirmed', cr)
#        return True

    @api.multi
    def wkf_create_purchase_history(self):
        history_obj = self.env['purchase.order.history']
        for purchase in self:
            history_obj.create({'purchase_id': purchase.id, 'date': time.strftime('%Y-%m-%d'), 'user_id': self._uid})
        return True

    @api.multi
    def wkf_confirm_order(self):
        history_obj = self.env['purchase.order.history']
        for po in self:
            if not po.history_ids:
                history_obj.create({'purchase_id': po.id, 'date': time.strftime('%Y-%m-%d'), 'user_id': self._uid})
                # Removed code refering to deprecated model
                # if self.env['res.partner.event.type'].check('purchase_open'):
                # self.env['res.partner.event'].create({'name':'Purchase Order: '+po.name, 'partner_id':po.partner_id.id, 'date':time.strftime('%Y-%m-%d %H:%M:%S'), 'user_id':uid, 'partner_type':'retailer', 'probability': 1.0, 'planned_cost':po.amount_untaxed})
        current_name = self.name_get()[0][1]
        self.write({'state': 'confirmed','validator': self._uid, 'approvator': self._uid}) #'approvator' : uid
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

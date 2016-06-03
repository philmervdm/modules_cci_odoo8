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

from openerp import models, fields, api, _

class translation_create_invoice(models.TransientModel):
    _name = 'translation.create.invoice'
    
    inv_created = fields.Char(string='Invoice Created', readonly=True)
    inv_rejected = fields.Char(string='Invoice Rejected', readonly=True)
    inv_rej_reason = fields.Text(string='Error Messages', readonly=True)
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_translation_rel', 'invoice_id', 'translation_id', 'Invoices')
    
    @api.multi
    def createInvoices(self):
        obj_transfolder = self.env['translation.folder']
        res = {}
        if self.env.context.get('active_ids', []):
            data_transfolder = obj_transfolder.browse(self.env.context['active_ids'])
            obj_lines = self.env['account.invoice.line']
            inv_create = 0
            inv_reject = 0
            inv_rej_reason = ""
            list_inv = []
            for transfolder in data_transfolder:
                address_contact = False
                address_invoice = False
                create_ids = []
                if transfolder.invoice_id:
                    inv_reject = inv_reject + 1
                    inv_rej_reason += "ID " + str(transfolder.id) + ": Already Has an Invoice Linked \n"
                    continue
        
                if transfolder.state <> 'confirmed':
                    inv_reject = inv_reject + 1
                    inv_rej_reason += "ID " + str(transfolder.id) + ": The Folder Isn't in 'Confirmed' State \n"
                    continue
        
                for add in transfolder.partner_id.child_ids:
                    if add.type == 'contact':
                        address_contact = add.id
                    if add.type == 'invoice':
                        address_invoice = add.id
                    if (not address_contact) and (add.type == 'default'):
                        address_contact = add.id
                    if (not address_invoice) and (add.type == 'default'):
                        address_invoice = add.id
        
                if not address_invoice:
                    inv_reject = inv_reject + 1
                    inv_rej_reason += "ID " + str(transfolder.id) + ": No Partner Address Defined on Partner \n"
                    continue
                inv_create = inv_create + 1
        
                translation_product = self.env['product.product'].search([('name', 'like', 'Translation Folder')], limit=1)
                fpos = transfolder.partner_id.property_account_position and transfolder.partner_id.property_account_position.id or False
                val = obj_lines.product_id_change(translation_product.id, False, partner_id=transfolder.partner_id.id, fposition_id=fpos)
                analytics_id = False
                if translation_product:
                    tmp = self.env['account.analytic.default'].search([('product_id', '=', translation_product.id)])
                    analytic_default_id = tmp and tmp[0] or False
                    if analytic_default_id:
                        analytics_id = self.env['account.analytic.default'].browse(analytic_default_id).analytics_id.id
        
                note = ''
                cci_special_reference = False
        
                if transfolder.awex_eligible and transfolder.awex_amount > 0:
                    note = 'AWEX intervention for a total of ' + str(transfolder.awex_amount)
                    cci_special_reference = "translation.folder*" + str(transfolder.id)
        
                inv_id = self.env['account.invoice.line'].create({
                    'name': 'Dossier traduction ' + transfolder.order_desc,
                    'account_id': val['value']['account_id'],
                    'price_unit': transfolder.base_amount,
                    'quantity': 1,
                    'discount': False,
                    'uos_id': val['value']['uos_id'],
                    'product_id': translation_product.id,
                    'analytics_id': analytics_id,
                    'invoice_line_tax_id': [(6, 0, val['value']['invoice_line_tax_id'])],
                    'note': transfolder.name + '\n\n' + note,
                    'cci_special_reference': cci_special_reference
                })
                inv = {
                    # 'name': transfolder.name,
                    'origin': transfolder.name,
                    'type': 'out_invoice',
                    'reference': False,
                    'account_id': transfolder.partner_id.property_account_receivable.id,
                    'partner_id': transfolder.partner_id.id,
                    'address_invoice_id':address_invoice,
                    'address_contact_id':address_contact,
                    'invoice_line': [(6, 0, [inv_id.id])],
                    'user_id': transfolder.partner_id.user_id and transfolder.partner_id.user_id.id or False,
                    'currency_id' :transfolder.partner_id.property_product_pricelist.currency_id.id,
                    'comment': '',
                    'payment_term':transfolder.partner_id.property_payment_term.id,
                    'fiscal_position': transfolder.partner_id.property_account_position.id,
#                     'domiciled': bool(transfolder.partner_id.domiciliation),
                }
                inv_obj = self.env['account.invoice']
                inv_id = inv_obj.create(inv)
                list_inv.append(inv_id.id)
                inv_id.signal_workflow('invoiced')
                transfolder.write({'invoice_id': inv_id.id})
                res.update({'inv_created': str(inv_create), 'invoice_ids':  [(6, 0, list_inv)], 'inv_rejected': str(inv_reject),  'inv_rej_reason': inv_rej_reason})
        return res 
    
    @api.model
    def default_get(self, fields):
        res = super(translation_create_invoice, self).default_get(fields)
        data = self.createInvoices()
        res.update(data)
        return res
        
    @api.multi
    def open_invoice(self):
        res = self.env.ref('account.invoice_form')
        return {
            'domain': "[('id','in', [" + ','.join(map(str, self.invoice_ids.ids)) + "])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False, 'tree'), (res.id, 'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
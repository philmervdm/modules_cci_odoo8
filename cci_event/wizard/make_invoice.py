    # -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _

class event_reg_make_invoice_cci(models.Model):
    _name = 'event.reg_make_invoice.cci'
    
    inv_created = fields.Char(string='Invoice Created', readonly=True)
    inv_rejected = fields.Char(string='Invoice Rejected', readonly=True)
    inv_rej_reason = fields.Text(string='Error Messages', readonly=True)
    invoice_ids = fiedls.Many2many('account.invoice', 'account_invoice_reg_rel', 'invoice_id', 'wizard_id', 'Invoices')
    
    @api.multi
    def makeInvoices(self):
        invoices = {}
        invoice_ids = []
        create_ids = []
    
        inv_create = 0
        inv_reject = 0
        inv_rej_reason = ""
        list_inv = []
        obj_event_reg = self.env['event.registration']
        data_event_reg = obj_event_reg.browse(self.env.context['active_ids'])
        obj_lines = self.env['account.invoice.line']
    
        for reg in data_event_reg:
            tax_ids = []
            if reg.state == 'draft':
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID " + str(reg.id) + ": Invoice cannot be created if the registration is in draft state. \n"
                continue
            if (not reg.tobe_invoiced):
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID " + str(reg.id) + ": Registration is set as 'Cannot be invoiced'. \n"
                continue
            if reg.invoice_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID " + str(reg.id) + ": Registration already has an invoice linked. \n"
                continue
            if not reg.event_id.product_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID " + str(reg.id) + ": Event related doesn't have any product defined. \n"
                continue
            if not reg.partner_invoice_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID " + str(reg.id) + ": Registration doesn't have any partner to invoice. \n"
                continue
            else:
                val_invoice = pool_obj.get('account.invoice').onchange_partner_id(cr, uid, [], 'out_invoice', reg.partner_invoice_id.id, False, False)
                val_invoice['value'].update({'partner_id': reg.partner_invoice_id.id})
                partner_address_id = val_invoice['value']['address_invoice_id']
    
            if not partner_address_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID " + str(reg.id) + ": Registered partner doesn't have an address to make the invoice. \n"
                continue
    
            inv_create = inv_create + 1
            value = obj_lines.product_id_change(reg.event_id.product_id.id, uom=False, partner_id=reg.partner_invoice_id.id, fposition_id=reg.partner_invoice_id.property_account_position.id)
            data_product = reg.event_id.product_id
            for tax in data_product.taxes_id:
                tax_ids.append(tax.id)
    
            vals = value['value']
#             c_name = reg.contact_id and ('-' + reg.contact_id.name_get()[0][1]) or ''
            c_name = ''
            vals.update({
                'name': reg.invoice_label + c_name,
                'price_unit': reg.unit_price,
                'quantity': reg.nb_register,
                'product_id':reg.event_id.product_id.id,
                'invoice_line_tax_id': [(6, 0, tax_ids)],
            })
            inv_line_ids = reg._create_invoice_lines(vals)
            val_invoice['value'].update({
                'origin': reg.invoice_label,
                'reference': False,
                'invoice_line': [(6, 0, [inv_line_ids])],
                'comment': '',
            })
    
            inv_obj = self.env['account.invoice']
            inv = inv_obj.create(val_invoice['value'])
            list_inv.append(inv.id)
            reg.write({'invoice_id' : inv_id, 'state':'done'})
#             reg._history('Invoiced', history=True)
    
        return {'inv_created' : str(inv_create) , 'inv_rejected' : str(inv_reject) , 'invoice_ids':  list_inv, 'inv_rej_reason': inv_rej_reason}
    
    def default_get(self, fields):
        res = super(event_reg_make_invoice_cci, self).default_get(fields)
        result = self.makeInvoices()
        res.update({
            'inv_created' : result['inv_created'],
            'inv_rejected' : result['inv_rejected'],
            'invoice_ids':  result['invoice_ids'],
            'inv_rej_reason': result['inv_rej_reason'],
        }) 
        return res
    
    @api.multi
    def list_invoice(self):
        model_data = self.env.ref('account.invoice_form')
        return {
            'domain': "[('id','in', [" + ','.join(map(str, self.invoice_ids.ids)) + "])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False, 'tree'), (mode_data.id, 'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }


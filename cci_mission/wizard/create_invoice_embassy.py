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

import time

class create_invoice_embassy(models.TransientModel):
    _name = 'create.invoice.embassy'
    
    inv_created =  fields.Char(string='Invoice Created',readonly=True)
    inv_rejected = fields.Char(string='Invoice Rejected',readonly=True)
    inv_rej_reason = fields.Text(string='Error Messages',readonly=True)
    invoice_ids = fields.Many2many('account.invoice', 'invoice_embassy_rel', 'invoice_id', 'embassy_id', 'Invoices')

    @api.multi
    def createInvoices(self):
        obj_embassy = self.env['cci_missions.embassy_folder']
        data_embassy = obj_embassy.browse(self.env.context.get('active_ids'))
        obj_lines = self.env['account.invoice.line']
        inv_create = 0
        inv_reject = 0
        inv_rej_reason = ""
        list_inv = []
        for embassy in data_embassy:
            address_contact = False
            address_invoice = False
            create_ids = []
    
#             if embassy.state != 'open':
#                 inv_reject = inv_reject + 1
#                 inv_rej_reason += "ID "+str(embassy.id)+": Check State. Folder should be Open for Invoicing. \n"
#                 continue
            if embassy.invoice_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID "+str(embassy.id)+": Already Has an Invoice Linked. \n"
                continue
            if not embassy.partner_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID "+str(embassy.id)+": Embassy Folder Does not Have any Partner to Invoice. \n"
                continue
            for add in embassy.partner_id.child_ids:
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
                inv_rej_reason += "ID "+str(embassy.id)+": No Partner Invoice Address Defined on Partner. \n"
                continue
            
            for line in embassy.embassy_folder_line_ids:
                tax_ids = []
                if line.tax_rate:
                    tax_ids.append(line.tax_rate.id)
                cci_special_reference = False
                note = ''
                analytics_id = False
                if line.awex_eligible and line.awex_amount > 0:
                    note = 'AWEX intervention for a total of ' + str(line.awex_amount)
                    cci_special_reference = "cci_missions.embassy_folder_line*" + str(line.id)
                
                if line.product_id:
                    tmp = self.env['account.analytic.default'].search([('product_id','=',line.product_id.id)])
                    analytic_default_id = tmp and tmp[0] or False
                    if analytic_default_id:
                        analytics_id = self.env['account.analytic.default'].browse(analytic_default_id).analytics_id.id
                
                inv_id = self.env['account.invoice.line'].create({
                        'name': embassy.name + ": " + line.name,
                        'account_id':line.account_id.id,
                        'price_unit': line.customer_amount,
                        'quantity': 1,
                        'discount': False,
                        'uos_id': False,
                        'product_id': line.product_id and line.product_id.id or False,
                        'invoice_line_tax_id': [(6,0,tax_ids)],
                        'note': note,
                        'cci_special_reference': cci_special_reference,
                        'analytics_id': analytics_id
                })
                create_ids.append(inv_id.id)
                
            inv = {
                    'origin': embassy.name,
                    'type': 'out_invoice',
                    'reference': embassy.customer_reference,
                    'account_id': embassy.partner_id.property_account_receivable.id,
                    'partner_id': embassy.partner_id.id,
#                     'address_invoice_id':address_invoice,
#                     'address_contact_id':address_contact,
                    'invoice_line': [(6,0,create_ids)],
                    'currency_id' :embassy.partner_id.property_product_pricelist.currency_id.id,# 1,
                    'comment': embassy.invoice_note,
                    'payment_term':embassy.partner_id.property_payment_term.id,
                    'fiscal_position': embassy.partner_id.property_account_position.id,
#                     'domiciled': bool(embassy.partner_id.domiciliation),
            }
            inv_create = inv_create + 1
            inv_obj = self.env['account.invoice']
            inv_id = inv_obj.create(inv)
            inv_id.button_reset_taxes()
            list_inv.append(inv_id.id)
            
            embassy.write({'state':'done','invoice_date': time.strftime('%Y-%m-%d %H:%M:%S')})
#             wf_service = netsvc.LocalService('workflow')
#             wf_service.trg_validate(uid, 'cci_missions.embassy_folder', embassy.id, 'done', cr)
            embassy.signal_workflow('done')
            embassy.write({'invoice_id' : inv_id.id})

        return {'inv_created' : str(inv_create) , 'inv_rejected' : str(inv_reject) ,'invoice_ids':  list_inv, 'inv_rej_reason': inv_rej_reason }

    @api.model
    def default_get(self, fields):
        res = super(create_invoice_embassy, self).default_get(fields)
        data = self.createInvoices()
        res.update(data)
        return res
    
    @api.multi
    def open_invoice(self):
        res = self.env.ref('account.invoice_form')
        
        val = {
            'domain': "[('id','in', [" + ','.join(map(str, self.invoice_ids.ids)) + "])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False,'tree'),(res.id,'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }
        return val

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


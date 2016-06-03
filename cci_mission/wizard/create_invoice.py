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
from openerp import models, fields , api , _
from openerp.exceptions import Warning

class create_invoice(models.TransientModel):
    _name = 'create.invoice'
    
    inv_created =  fields.Char(string='Invoice Created',readonly=True)
    inv_rejected = fields.Char(string='Invoice Rejected',readonly=True)
    inv_rej_reason = fields.Text(string='Error Messages',readonly=True)
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_mission_rel', 'invoice_id', 'mission_id', 'Invoices')
    
    @api.multi
    def createInvoices(self):
        list_inv = []
        obj_dossier = self.env[self.env.context.get('active_model')]
        current_model = self.env.context.get('active_model')
        data_dossier = obj_dossier.browse(self.env.context.get('active_ids'))
        obj_lines = self.env['account.invoice.line']
        inv_create = 0
        inv_reject = 0
        inv_rej_reason = ""
    
        ctx = self.env.context.copy()
        for data in data_dossier:
            ctx.update({'pricelist': data.order_partner_id.property_product_pricelist.id})
            list = []
            value = []
            dict = {}
            address_contact = False
            address_invoice = False
            create_ids = []
            if data.invoice_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID "+str(data.id)+": Already Has an Invoice Linked. \n"
                continue
    
            if not data.to_bill:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID "+str(data.id)+": Cannot Be Billed. \n"
                continue
            for add in data.order_partner_id.child_ids:
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
                inv_rej_reason += "ID "+str(data.id)+": No Partner Address Defined on Billed Customer. \n"
                continue
    
            ctx.update({'date':data.date})
            inv_create = inv_create + 1
            fpos = data.order_partner_id.property_account_position and data.order_partner_id.property_account_position.id or False
    
            for lines in data.product_ids :
                val = obj_lines.product_id_change(lines.product_id.id,False, partner_id=data.order_partner_id.id, fposition_id=fpos)
                if lines.product_id:
                    tmp = self.env['account.analytic.default'].search([('product_id','=',lines.product_id.id)])
                    analytic_default_id = tmp and tmp[0] or False
                    if analytic_default_id:
                        analytics_id = self.env['account.analytic.default'].browse(analytic_default_id).analytics_id.id
                        val['value'].update({'analytics_id': analytics_id})
                        
                val['value'].update({'name':lines.name})
                val['value'].update({'account_id':lines.account_id.id})
                val['value'].update({'product_id' : lines.product_id.id })
                val['value'].update({'quantity' : lines.quantity })
                val['value'].update({'uos_id':lines.uos_id.id})
                val['value'].update({'price_unit':lines.price_unit})
                sale_taxes = []
                if lines.taxes_id:
                    map(lambda x:sale_taxes.append(x.id),lines.taxes_id)
                    
                val['value'].update({'invoice_line_tax_id': [(6, 0, sale_taxes)]})
                value.append(val)
    
            list.append(data.type_id.original_product_id.id)
            dict['original'] = data.type_id.original_product_id.id
            list.append(data.type_id.copy_product_id.id)
            dict['copy'] = data.type_id.copy_product_id.id
            for prod_id in list:
                val = obj_lines.product_id_change(prod_id,False, partner_id=data.order_partner_id.id, fposition_id=fpos)
                val['value'].update({'product_id' : prod_id })
                val['value'].update({'invoice_line_tax_id': [(6, 0, val['value']['invoice_line_tax_id'])]})
    
                force_member=force_non_member=False
                if current_model=='cci_missions.legalization':
                    if data.member_price==1:
                        force_member=True
                    else:
                        force_non_member=True
                ctx.update({'partner_id':data.order_partner_id.id})
                ctx.update({'force_member':force_member})
                ctx.update({'force_non_member':force_non_member})
                ctx.update({'value_goods':data.goods_value})
                ctx.update({'date':data.date})
                price = self.env['product.product'].browse(prod_id).with_context(ctx)._product_price(False, False)
                val['value'].update({'price_unit':price[prod_id]})
    
                if prod_id == dict['original']:
                    val['value'].update({'quantity' : data.quantity_original})
                else:
                    val['value'].update({'quantity' : data.quantity_copies})
                value.append(val)
    
            for val in value:
                if val['value']['quantity']>0.00:
                    if val['value']['product_id'] != False:
                        val['value']['name'] = data.text_on_invoice + ': ' + val['value']['name']
                        inv_id = self.env['account.invoice.line'].create(val['value'])
                    else:
                        raise Warning('Input Error!','No Product Chosen')
                    create_ids.append(inv_id.id)
            inv = {
                'origin': data.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': data.order_partner_id.property_account_receivable.id,
                'partner_id': data.order_partner_id.id,
#                 'address_invoice_id':address_invoice,
#                 'address_contact_id':address_contact,
                'invoice_line': [(6,0,create_ids)],
                'currency_id' :data.order_partner_id.property_product_pricelist.currency_id.id,# 1,
                'payment_term':data.order_partner_id.property_payment_term.id,
                'fiscal_position': data.order_partner_id.property_account_position.id,
#                 'domiciled': bool(data.order_partner_id.domiciliation),
                }
            price = data.total
            inv_obj = self.env['account.invoice']
            inv_id = inv_obj.create(inv)
            list_inv.append(inv_id.id)
            
#             wf_service = netsvc.LocalService('workflow')
#             wf_service.trg_validate(uid, current_model, data.id, 'invoiced', cr)
            
            data.signal_workflow('invoiced')
            
            inv_id.button_reset_taxes()
            data.write({'invoice_id' : inv_id.id, 'invoiced_amount':price})
    
        return {'inv_created' : str(inv_create) , 'inv_rejected' : str(inv_reject) , 'invoice_ids':  list_inv, 'inv_rej_reason': inv_rej_reason}



    @api.model
    def default_get(self, fields):
        res = super(create_invoice, self).default_get(fields)
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


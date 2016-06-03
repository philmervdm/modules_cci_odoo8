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

class create_invoice_carnet(models.TransientModel):
    
    _name = 'create.invoice.carnet'
    
    inv_created =  fields.Char(string='Invoice Created',readonly=True)
    inv_rejected = fields.Char(string='Invoice Rejected',readonly=True)
    inv_rej_reason = fields.Text(string='Error Messages',readonly=True)
    invoice_ids = fields.Many2many('account.invoice', 'invoice_cranet_rel', 'invoice_id', 'carnet_id', 'Invoices')

    @api.multi
    def createInvoices(self):
        obj_carnet = self.env[self.env.context.get('active_model')]
        data_carnet = obj_carnet.browse(self.env.context.get('active_ids'))
        obj_lines = self.env['account.invoice.line']
        inv_create = 0
        inv_reject = 0
        inv_rej_reason = ""
        list_inv = []
        
        ctx = self.env.context.copy()
        for carnet in data_carnet:
            ctx.update({'pricelist': carnet.partner_id.property_product_pricelist.id})
            list = []
            value = []
            address_contact = False
            address_invoice = False
            create_ids = []
            if carnet.invoice_id:
                inv_reject = inv_reject + 1
                inv_rej_reason += "ID "+str(carnet.id)+": Already Has an Invoice Linked \n"
                continue
    
            ctx.update({'date':carnet.creation_date})
            list.append(carnet.type_id.original_product_id.id)
            list.append(carnet.type_id.copy_product_id.id)
            
            if not carnet.own_risk:
                list.append(carnet.warranty_product_id.id)
            fpos = carnet.partner_id.property_account_position and carnet.partner_id.property_account_position.id or False
            
            for product_line in carnet.product_ids:#extra Products
                val = obj_lines.product_id_change(product_line.product_id.id,False, partner_id=carnet.partner_id.id, fposition_id=fpos)
                if product_line.product_id:
                    tmp = self.env['account.analytic.default'].search([('product_id','=',product_line.product_id.id)])
                    analytic_default_id = tmp and tmp[0] or False
                    if analytic_default_id:
                        analytics_id = self.env['account.analytic.default'].browse(analytic_default_id).analytics_id.id
                        val['value'].update({'analytics_id': analytics_id})
                        
                val['value'].update({'product_id' : product_line.product_id.id })
                val['value'].update({'quantity' : product_line.quantity })
                val['value'].update({'price_unit':product_line.price_unit})
                sale_taxes = []
                if product_line.taxes_id:
                    map(lambda x:sale_taxes.append(x.id),product_line.taxes_id)
                val['value'].update({'invoice_line_tax_id': [(6,0,sale_taxes)]})
                value.append(val)
    
            for add in carnet.partner_id.child_ids:
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
                inv_rej_reason += "ID "+str(carnet.id)+": No Partner Address Defined on Partner \n"
                continue
            inv_create = inv_create + 1
            count=0
            for prod_id in list:
                count += 1
                val = obj_lines.product_id_change(prod_id,False, partner_id=carnet.partner_id.id, fposition_id=fpos)
                val['value'].update({'product_id': prod_id })
                val['value'].update({'invoice_line_tax_id': [(6, 0, val['value']['invoice_line_tax_id'])]})
                if count==2:
                    qty_copy=carnet.initial_pages
                    if qty_copy<0:
                        qty_copy=0
                    val['value'].update({'quantity' : qty_copy })
                else:
                    val['value'].update({'quantity' : 1 })
                force_member=force_non_member=False
                if carnet.member_price==1:
                    force_member=True
                else:
                    force_non_member=True
                    
                ctx.update({'partner_id':carnet.partner_id.id})
                ctx.update({'force_member':force_member})
                ctx.update({'force_non_member':force_non_member})
                ctx.update({'value_goods':carnet.goods_value})
                ctx.update({'double_signature':carnet.double_signature})
                ctx.update({'date':carnet.creation_date})
                ctx.update({'emission_date':carnet.creation_date})
                price = self.env['product.product'].browse(prod_id).with_context(ctx)._product_price(False, False)
                val['value'].update({'price_unit':price[prod_id]})
                value.append(val)

            for val in value:
                if val['value']['quantity']>0.00:
                    val['value']['name'] = carnet.name + ": " + val['value']['name']
                    inv_id = self.env['account.invoice.line'].create(val['value'])
                    create_ids.append(inv_id.id)
            inv = {
                    'origin': carnet.name,
                    'type': 'out_invoice',
                    'reference': False,
                    'account_id': carnet.partner_id.property_account_receivable.id,
                    'partner_id': carnet.partner_id.id,
#                     'address_invoice_id':address_invoice,
#                     'address_contact_id':address_contact,
                    'invoice_line': [(6,0,create_ids)],
                    'currency_id' :carnet.partner_id.property_product_pricelist.currency_id.id,# 1,
                    'comment': '',
                    'payment_term':carnet.partner_id.property_payment_term.id,
                    'fiscal_position': carnet.partner_id.property_account_position.id,
#                     'domiciled': bool(carnet.partner_id.domiciliation),
                }
    
            inv_obj = self.env['account.invoice']
            inv_id = inv_obj.create(inv)
            inv_id.button_reset_taxes()
            list_inv.append(inv_id.id)
            
#             wf_service = netsvc.LocalService('workflow')
#             wf_service.trg_validate(uid, 'cci_missions.ata_carnet', carnet.id, 'created', cr)
            
            carnet.signal_workflow('created')
            carnet.write({'invoice_id' : inv_id.id})
    
        return {'inv_created' : str(inv_create),'inv_rejected' : str(inv_reject)  ,'invoice_ids': list_inv,  'inv_rej_reason': inv_rej_reason }


    @api.model
    def default_get(self, fields):
        res = super(create_invoice_carnet, self).default_get(fields)
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
            'views': [(False,'tree'),(res.id,'form')],
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


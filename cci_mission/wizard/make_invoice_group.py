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
import time

import create_invoice_carnet
import create_invoice_embassy
import create_invoice
# from event.wizard import make_invoice

class make_invocie_group(models.TransientModel):
    _name = 'make.invoice.group'
    
    registration = fields.Boolean(string = 'Include Events Registrations')
    date_invoice = fields.Date(string = 'Date Invoiced', default = time.strftime('%Y-%m-%d'), help = 'You can set here the value to put in the field "date invoiced" of the invoice. Moreover, this date will be an additional criterion for the objects to invoice search.')
    period_id = fields.Many2one('account.period', string = 'Force Invoice Period (keep empty to use current period)')
    invoice_title = fields.Char(string = 'Invoices Title', help = 'You can specify here a title for the created invoice, that will fill the origin field')

    @api.multi
    def group_invoice(self):
        date_inv = self.date_invoice
        data_invoice_title = self.invoice_title
        force_period = self.period_id.id
        today_date = time.strftime('%Y-%m-%d')
        obj_inv = self.env['account.invoice']
        dict_info=[]
        models=['cci_missions.certificate','cci_missions.legalization','cci_missions.embassy_folder','cci_missions.ata_carnet']
        
        if self.registration:
            models.append('event.registration')
    
        for model in models:
            if model == 'cci_missions.embassy_folder' or model == 'event.registration':
                state_to_check = 'open'
            else:
                state_to_check = 'draft'
            if model == 'event.registration':
                date_to_check = 'event_id.date_begin'
            elif model == 'cci_missions.ata_carnet':
                date_to_check = 'creation_date'
            elif model == 'cci_missions.embassy_folder':
                date_to_check = 'create_date'
            else:
                date_to_check = 'date'
    
            try:
                model_ids = self.env[model].search([('state','=', state_to_check), (date_to_check, '<=', self.date_invoice)])
            except Exception ,e:
                model_ids = self.env[model].search([('stage_id.name','=', state_to_check), (date_to_check, '<=', self.date_invoice)])
    
            if model_ids:
                read_ids = model_ids.read(['partner_id','order_partner_id','date','creation_date','partner_invoice_id'])
                for element in read_ids:
                    part_info={}
                    if ('partner_id' in element) and element['partner_id']:
                        part_info['partner_id'] = element['partner_id'][0]
                        part_info['id'] = element['id']
                        part_info['model'] = model
    
                    if ('order_partner_id' in element) and element['order_partner_id']:
                        part_info['partner_id'] = element['order_partner_id'][0]
                        part_info['id'] = element['id']
                        part_info['model'] = model
    
                    if ('partner_invoice_id' in element) and element['partner_invoice_id']:
                        part_info['partner_id'] = element['partner_invoice_id'][0]
                        part_info['id'] = element['id']
                        part_info['model'] = model
    
                    if 'date' in element:
                        part_info['date'] = element['date']
    
                    if 'creation_date' in element:
                        part_info['date'] = element['creation_date']
    
                    if part_info and part_info.has_key('partner_id'):
                        dict_info.append(part_info)
        if not dict_info:
            ctx = self.env.context.copy()
            invoice_ids = []
            if self.registration:
                message = "No invoices grouped  because no invoices for ATA Carnet, Legalizations, Certifications and (Embassy Folders and Registrations) are in 'Draft' state."
            else:
                message ="No invoices grouped  because no invoices for ATA Carnet, Legalizations, Certifications and Embassy Folders are in 'Draft' state."
            ctx['invoice_ids'] = invoice_ids
            ctx['message'] = message
            return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mission.group.invoice',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': ctx,
                }
        
        partner_ids = list(set([x['partner_id'] for x in dict_info]))
        partner_ids.sort()
        disp_msg=''
    
        list_invoice=[]
        for partner_id in partner_ids:
            partner = self.env['res.partner'].browse(partner_id)
            final_info={}
            list_info=[]
            list_invoice_ids=[]
            self.invoice_info=[]
            for element in dict_info:
                final_info={}
                if element['partner_id']==partner_id:
                    data={'model':element['model'],'form':{},'id':element['id'],'ids':[element['id']],'report_type': 'pdf'}
                    final_info['ids']=[]
                    final_info['date']=element['date'][0:10]
    
                    if element['model']=='cci_missions.ata_carnet':
                        ctx = self.env.context.copy()
                        ctx['active_model'] = element['model']
                        ctx['active_ids'] = [element['id']]
                        result=self.env['create.invoice.carnet'].with_context(ctx).createInvoices()
    
                        if result['inv_rejected']>0 and result['inv_rej_reason']:
                            disp_msg +='\nFor Partner '+ partner.name +' On ATA Carnet with ' + result['inv_rej_reason']
                            continue
                        if result['invoice_ids']:
                            list_invoice_ids.append(result['invoice_ids'][0])
                            final_info['ids'].append(result['invoice_ids'][0])
                            list_info.append(final_info)
                            final_info={}
                            final_info['id']=element['id']
                            final_info['model']=element['model']
                            self.invoice_info.append(final_info)
    
                    if element['model']=='cci_missions.embassy_folder':
                        ctx = self.env.context.copy()
                        ctx['active_model'] = element['model']
                        ctx['active_ids'] = [element['id']]
                        result=self.env['create.invoice.embassy'].with_context(ctx).createInvoices()
    
                        if result['inv_rejected']>0 and result['inv_rej_reason']:
                            disp_msg +='\nFor Partner '+ partner.name +' On Embassy Folder with ' + result['inv_rej_reason']
                            continue
                        if result['invoice_ids']:
                            list_invoice_ids.append(result['invoice_ids'][0])
                            final_info['ids'].append(result['invoice_ids'][0])
                            list_info.append(final_info)
                            final_info={}
                            final_info['id']=element['id']
                            final_info['model']=element['model']
                            self.invoice_info.append(final_info)
    
                    if element['model'] in ('cci_missions.certificate','cci_missions.legalization'):
                        ctx = self.env.context.copy()
                        ctx['active_model'] = element['model']
                        ctx['active_ids'] = [element['id']]
                        result = self.env['create.invoice'].with_context(ctx).createInvoices()
    
                        if result['inv_rejected']>0 and result['inv_rej_reason']:
                            disp_msg +='\nFor Partner '+ partner.name +' On Certificate or Legalization with ' + result['inv_rej_reason']
                            continue
                        if result['invoice_ids']:
                            list_invoice_ids.append(result['invoice_ids'][0])
                            final_info['ids'].append(result['invoice_ids'][0])
                            list_info.append(final_info)
                            final_info={}
                            final_info['id']=element['id']
                            final_info['model']=element['model']
                            self.invoice_info.append(final_info)
    
                    if element['model']=='event.registration':
                        result = make_invoice._makeInvoices()
    
                        if result['inv_rejected']>0 and result['inv_rej_reason']:
                            disp_msg +='\nFor Partner '+ partner.name +' On Event Registration ' + result['inv_rej_reason']
                            continue
                        if result['invoice_ids']:
                            list_invoice_ids.append(result['invoice_ids'][0])
                            final_info['ids'].append(result['invoice_ids'][0])
                            list_info.append(final_info)
                            final_info={}
                            final_info['id']=element['id']
                            final_info['model']=element['model']
                            self.invoice_info.append(final_info)
    
            done_date=[]
            date_id_dict={}
            done_date=list(set([x['date'] for x in list_info]))
            done_date.sort()
            final_list=[]
            for date in done_date:
                date_id_dict={}
                date_id_dict['date']=date
                date_id_dict['ids']=[]
                for item in list_info:
                    if date==item['date']:
                        date_id_dict['ids'] +=item['ids']
                final_list.append(date_id_dict)
    
            count=0
            list_inv_lines=[]
            #marked
            if not final_list:
                continue
            for record in final_list:
                customer_ref = record['date']
                line_obj = self.env['account.invoice.line']
                id_note=line_obj.create({'name':customer_ref,'state':'title','sequence':count})
                count=count+1
                list_inv_lines.append(id_note.id)
                data_inv=obj_inv.browse(record['ids'])
                notes = ''
                for invoice in data_inv:
                    if invoice.reference:
                        customer_ref = customer_ref +' ' + invoice.reference
                    if invoice.comment:
                        notes = (notes + ' ' + invoice.comment)
    
                    for line in invoice.invoice_line:
                        if invoice.name:
                            name = invoice.name +' '+ line.name
                        else:
                            name = line.name
                        taxe_ids = map(lambda x: x.id, line.invoice_line_tax_id)
                        args =  {
                             'name': name,
                             'account_id':line.account_id.id,
                             'price_unit': line.price_unit,
                             'quantity': line.quantity,
                             'discount': False,
                             'uos_id': line.uos_id.id,
                             'product_id':line.product_id.id,
                             'invoice_line_tax_id': [(6, 0, taxe_ids)],
#                              'note':line.note,
                             'sequence' : count,
                            'cci_special_reference': line.cci_special_reference,
                            'analytics_id': line.analytics_id and line.analytics_id.id,
                        }
                        inv_line = line_obj.create(args)
                        count=count+1
                        list_inv_lines.append(inv_line.id)
        #            If we want to cancel ==> obj_inv.write(cr,uid,invoice.id,{'state':'cancel'}) here
        #            If we want to delete ==> obj_inv.unlink(cr,uid,list_invoice_ids) after new invoice creation.
    
#                 id_note.write({'name':customer_ref})
#                 id_note1=line_obj.create({'name':notes,'state':'text','sequence':count})# a new line of type 'note' with all the old invoice note
#                 count=count+1
#                 list_inv_lines.append(id_note1.id)
#                 id_linee=line_obj.create({'state':'line','sequence':count}) #a new line of type 'line'
#                 count=count+1
#                 list_inv_lines.append(id_linee.id)
#                 id_stotal=line_obj.create({'name':'Subtotal','state':'subtotal','sequence':count})#a new line of type 'subtotal'
#                 count=count+1
#                 list_inv_lines.append(id_stotal.id)
            #end-marked
            inv = {
                    'origin': data_invoice_title,
                    'type': 'out_invoice',
                    'reference': False,
                    'account_id': invoice.account_id.id,
                    'partner_id': invoice.partner_id.id,
                    'user_id': invoice.partner_id.user_id and invoice.partner_id.user_id.id or False,
#                     'address_invoice_id':invoice.address_invoice_id.id,
#                     'address_contact_id':invoice.address_contact_id.id,
                    'invoice_line': [(6,0,list_inv_lines)],
                    'currency_id' :invoice.currency_id.id,# 1
                    'comment': "",
                    'payment_term':invoice.payment_term.id,
                    'date_invoice':date_inv or today_date,
                    'period_id':force_period or False,
                    'fiscal_position': invoice.partner_id.property_account_position.id,
                    'domiciled': bool(invoice.partner_id.domiciliation),
                }
            inv_id = obj_inv.create(inv)
            inv_id.button_reset_taxes()
            for item in self.invoice_info:
                self.env[item['model']].browse(item['id']).write({'invoice_id' : inv_id.id})
            disp_msg +='\n'+ partner.name + ': '+ str(len(data_inv)) +' Invoice(s) Grouped.'
            list_invoice.append(inv_id.id)
            self.env['account.invoice'].browse(list_invoice_ids).unlink()
        
        ctx = self.env.context.copy()
        ctx['invoice_ids'] = list_invoice
        ctx['message'] = disp_msg
        return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mission.group.invoice',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': ctx,
                }
        
class mission_group_invoice(models.TransientModel):
    _name = 'mission.group.invoice'
    
    message = fields.Text(string='', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(mission_group_invoice,self).default_get(fields)
        res['message'] = self.env.context.get('message')
        return res
    
    @api.multi
    def list_invoice(self):
        res = self.env.ref('account.invoice_form')
        return {
            'domain': "[('id','in', ["+','.join(map(str,self.env.context.get('invoice_ids',[])))+"])]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False,'tree'), (res.id,'form')],
            'context': "{'type':'out_invoice',}",
            'type': 'ir.actions.act_window'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

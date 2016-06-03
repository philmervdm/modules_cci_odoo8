# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

class event_partner_registration(models.Model):
    _name = 'event.partner.registration'
    
    event_id =  fields.Many2one('event.event', string='Event', required=True)
    #function_id = fields.Many2one('res.partner.function', string='Function', required=True)
    function_id = fields.Char('Function')
    
    @api.multi
    def create_reg(self):
        obj_reg = self.env['event.registration']
        obj_fun = self.env['res.partner.function']
#         function = obj_fun.browse([data['form']['function_id']], context=context)[0].code
        obj_event = self.env['event.event']
        obj_part = self.env['res.partner']
        event = self.event_id
        reg_ids = []
        part_dict = {}
        contact_ids = []
        filter_contacts = []
        
        for part in obj_part.browse(self.env.context('active_ids')):
            for add in part.child_ids:
                for job in add.other_contact_ids:
                    if job.function_code_label == self.function_id:
                        part_dict[part.id] = job.contact_id.id
                        contact_ids.append(job.contact_id.id)
                        break
    
        if contact_ids:
            self.env.cr.execute('select e.id, e.partner_id from event_registration as e  \
                    left join res_partner as c on c.id=e.partner_id \
                    where e.event_id = %s and c.id in ('+','.join(map(str, contact_ids))+') \
                    group by e.contact_id,e.id', (event.id,))
            regs = self.env.cr.dictfetchall()
            if regs:
                map(lambda x: filter_contacts.append(x['contact_id']), regs)
    
#         contacts_list = []
        for part, contact in part_dict.items():
            if contact in filter_contacts or contact in contacts_list:
                continue
            data = event._onchange_partner()
#             data2 = obj_reg.onchange_contact_id(contact, part)
#             data['value'].update(data2['value'])
            data = data['value']
    
            data.update({'event_id': event.id,
                'partner_id': part,
#                 'contact_id': contact,
                'invoice_label': event.product_id.name,
                'name': _('Registration')
            })
            reg_id = obj_reg.create(data)
            contacts_list.append(contact)
            reg_ids.append(reg_id.id)
            
        ctx = self.env.context.copy()
        ctx.update({'reg_ids': reg_ids})
        resource = self.env.ref('cci_event.event_partner_registration_msg_view')
        return {
            'name': 'Result',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.confirm.registrations.msg',
            'views': [(resource.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
        
class event_partner_registration_msg(models.Model):
    _name = 'event.partner.registration.msg'
    
    @api.multi
    def open_reg(self):
        case_ids = []
        if self.env.context.get('reg_ids', []):
            self.env.cr.execute('select case_id from event_registration where id in ('+','.join(map(str, self.env.context['reg_ids']))+')')
            map(lambda x:case_ids.append(x[0]), self.env.cr.fetchall())
        
        model_data = self.env.ref('event.view_event_registration_form')
        return {
            'domain': "[('id','in', ["+','.join(map(str, case_ids))+"])]",
            'name': 'Registrations',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.registration',
            'views': [(False,'tree'), (model_data.id,'form')],
            'type': 'ir.actions.act_window'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
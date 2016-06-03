# -*- coding: utf-8 -*-

from openerp import api, fields, models, _


class create_histo_from_interest(models.TransientModel):
    _name = 'create.histo.from.interest'
    
    @api.multi
    def copy_todo_to_histo(self):
        res_id = False
        
        todo_obj = self.env['crm_cci.todo']
        todo = todo_obj.browse(self.env.context.get('active_id'))
        if todo.action and todo.action != '/':
            histo_obj = self.env['res.partner.history']
            contact_cci_id = False
            if todo.cci_contact_follow:
                contact_obj = self.env['cci.contact']
                contact_ids = contact_obj.search([('user','=',todo.cci_contact_follow.id)])
                if contact_ids:
                    contact_cci_id = contact_ids[0]
            if not contact_cci_id:
                # No cci_contact_follow on the todo => by default we use the cci_contact
                contact_cci_id = ( todo.cci_contact and todo.cci_contact.id or 0 )
            values  = {'partner': todo.partner and todo.partner.id or 0,
                       #'date': todo.date,  # they prefer 'today'
                       'product': todo.product and todo.product.id or 0,
                       'category': todo.category and todo.category.id or 0,
                       'next_action': False,
                       'cci_contact_follow': False,
                       'description': todo.description,
                       'case_id':0,
                       'cci_contact': contact_cci_id,
                       'contact': todo.contact and todo.contact.id or 0,
                       'action': todo.action,
                       'state': 'closed',
                      }
            res_id = histo_obj.create(values)
        if res_id:
            value = {
                'name': "Create History From Interest",
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'res.partner.history',
                'res_id': [res_id],
                'type': 'ir.actions.act_window',
            }
            return value
        else:
            return True
    

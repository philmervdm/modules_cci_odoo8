# -*- coding: utf-8 -*-

from openerp import api, fields, models, _

class create_histo_from_mark(models.TransientModel):
    _name = 'create.histo.from.mark'
    
    action = fields.Selection([
                 ('appel_sortant','Appel sortant'),
                 ('appel_entrant','Appel entrant'),
                 ('commando','Commando'),
                 ('mail','Mail'),
                 ('site','Site Internet'),
                 ('meeting_cci','Meeting CCI'),
                 ('meeting_externe','Meeting externe'),
                 ('midi','Midi'),
                 ('rdv','RDV')], string='Action', required=True)
    
    @api.multi
    def copy_mark_to_histo(self):
        res_id = False
        
        mark_obj = self.env['res.partner.interest']
        mark = mark_obj.browse(self.env.context.get('active_id'))
        histo_obj = self.env['res.partner.history']
        values  = {'partner': mark.partner and mark.partner.id or 0,
                   'product': mark.product and mark.product.id or 0,
                   'category': mark.category and mark.category.id or 0,
                   'next_action': False,
                   'cci_contact_follow': False,
                   'description': mark.description,
                   'case_id':0,
                   'cci_contact': mark.cci_contact and mark.cci_contact.id or 0,
                   'contact': mark.contact and mark.contact.id or 0,
                   'action': self.action,
                   'state': 'closed',
                  }
        res_id = histo_obj.create(values)
        value = {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner.history',
            'res_id': [],
            'type': 'ir.actions.act_window',
        }
        if res_id:
            value['res_id'] = res_id.id
        return value
    

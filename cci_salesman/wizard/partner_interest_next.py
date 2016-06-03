# -*- coding: utf-8 -*-
from openerp import api, fields, models, _

class partner_interest_next(models.TransientModel):
    _name = 'partner.interest.next'

    @api.multi
    def do_next(self):
        partner_obj = self.env['res.partner']
        interest_obj = self.env['res.partner.interest']
#         interest_next_obj = self.env['res.partner.interest.next']    
        
        for partner in partner_obj.browse(self.ids):
            partner.write({'year': partner.year + 1})
            for interest in partner.interest_year:
                interest.unlink()
            for interest_next in partner.interest_next_year:      
                self.next = True
                interest_obj.create( 
                    {'partner': interest_next.partner.id,
                     'date': interest_next.date,
                     'product': interest_next.product.id,
                     'cci_contact': interest_next.cci_contact.id,
                     'contact': interest_next.contact.id,
                     'category': interest_next.category.id,
                     'turnover_hoped': interest_next.turnover_hoped,
                     'next_action': interest_next.next_action,
                     'cci_contact_follow': interest_next.cci_contact_follow.id,
                     'description': interest_next.description,
                    })
                interest_next.unlink()
            
        return {}

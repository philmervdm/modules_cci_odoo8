# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import api, fields, models, _
from openerp.exceptions import Warning

class partner_interest_order(models.TransientModel):
    _name = 'partner.interest.order'

    @api.multi
    def do_order(self):
        
        model = False
        res_id = False
        
        if self.env.context.get('active_model') == 'res.partner.interest':
            interest_obj = self.env['res.partner.interest']
        else:
            interest_obj = self.env['res.partner.interest.next']
        
        interest = interest_obj.browse(self.id)

        if interest.product and interest.product.order_type and \
            interest.partner:
            if interest.product.order_type == 'participation' and \
                interest.contact:
                model = 'cci_club.participation'
                participation_obj =self.env['cci_club.participation']
                participation_state_obj = self.env['cci_club.participation_state']
                state = participation_state_obj.search([('name', '=', 'EN ATTENTE DE GROUPE')])[0]
                
                values  = {'partner_id': interest.partner.id,
                           'contact_id': interest.contact.contact_id.id,
                           'provided_turnover': interest.turnover_hoped,
                           'state_id': state,
                           'salesman': interest.partner.user_id.id}
                
                res_id = participation_obj.create(values)

                values = participation_obj.onchange_partner([res_id], 
                                                interest.partner.id, False,
                                                interest.contact.contact_id.id)
                participation_obj.write([res_id], values['value'])
                
            elif interest.product.order_type == 'order' and \
                interest.category and interest.category.product:
                model = 'sale.order'
                order_obj = self.env['sale.order']
                order_line_obj = self.env['sale.order.line']
                
                values  = {'partner_id': interest.partner.id}
                values.update(order_obj.onchange_partner_id( 
                                    False, interest.partner.id)['value'])
                res_id = order_obj.create(values)
                
                values = order_line_obj.product_id_change(False, 
                                    False, interest.category.product.id, qty=1, 
                                    partner_id=interest.partner.id)['value']
                                    
                values.update({'order_id': res_id,
                               'product_id': interest.category.product.id,
                               'price_unit': interest.turnover_hoped})
                order_line_obj.create(values)

            elif interest.product.order_type == 'membership':
                model = 'res.partner'
                partner_obj = self.env['res.partner']
            else:
                raise Warning(_('Erreur !'),
                    _('Des donnees sont manquantes.'))
                
            interest_obj.write(self.id, {'turnover_hoped': 0})
        
        value = {}
        
        if model and res_id:
            value = {
                'name': "Marques d'interets: BDC",
                'domain': "[]",
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': model,
                'res_id': [res_id],
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
            
        return value

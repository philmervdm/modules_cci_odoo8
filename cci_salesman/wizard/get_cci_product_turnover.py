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
# Version 1.0 Philmer
from openerp import api, fields, models, _

class get_cci_product_turnover(models.TransientModel):
    _name="get.cci.product.turnover"
    
    date_from = fields.Integer(string='From Year', requred=True)
    to = fields.Integer(string='To Year', requred=True) 
    
    @api.multi
    def calculate_turnover(self):
        if self.date_from > self.to:
            date_from = self.to
            date_to   = self.date_from
        else:
            date_from = self.date_from
            date_to   = self.to
        current_partner_id = self.env.context.get('active_id')
        #action_ids = obj_history.search(cr,uid,[('date','>=',date_from),('date','<=',date_to),('state','=','closed')])
        #actions = obj_history.read(cr,uid,action_ids,['action','cci_contact'])
        turnover_obj = self.env['cci.turnover']
            
        # remove all turnovers for this partner
        all_turnovers = turnover_obj.search([('partner','=',current_partner_id)])
        all_turnovers.unlink()
        
        self.env.cr.execute("""
            SELECT cp.id AS product_name,
                ai.partner_id,
                date_part('year', ai.date_invoice) AS date_year,
                SUM(ail.price_subtotal) AS total
            FROM account_invoice ai
                INNER JOIN account_invoice_line ail
                    ON ai.id = ail.invoice_id
                INNER JOIN product_product p
                    ON ail.product_id = p.id
                INNER JOIN cci_product cp
                    ON p.cci_product_id = cp.id
            WHERE ai.state in ('open', 'paid') and ai.type in ('out_invoice','out_refund') and ai.partner_id = %s
            GROUP BY cp.id, ai.partner_id, date_year
        """ % current_partner_id ) 
        lines = self.env.cr.fetchall()
            
        for line in lines:
            # create new turnover records
            data = {'cci_product': line[0],
                    'partner': line[1],
                    'sum_price': line[3],
                    'years': line[2],
                   }
            turnover_id = turnover_obj.create(data)
        value = {
                'domain': [('partner', '=', current_partner_id)],
                'name': _('Annual TurnOver by CCI Product'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'cci.turnover',
                'type': 'ir.actions.act_window',
            }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    
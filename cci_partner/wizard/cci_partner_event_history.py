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

import time
from openerp import models, fields, api, _

class cci_event_history(models.TransientModel):
    _name = 'cci.event.history'
    
    user_id = fields.Many2one('res.users', string='User')
    name = fields.Char(string='Events', size=64, required=True)
    probability = fields.Float(string='Probability (0.50)')
    canal_id = fields.Many2one('crm.tracking.source', string='Chanel')
    type = fields.Selection([('sale', 'Sale Opportunity'), ('purchase', 'Purchase Offer'), ('prospect', 'Prospect Contact')], string='Type of Event')
    planned_cost = fields.Float(string='Planned Cost')
    description = fields.Text(string='Description')
#     som = fields.Many2one('res.partner.som', string='State of Mind')
    partner_type = fields.Selection([('customer', 'Customer'), ('retailer', 'Retailer'), ('prospect', 'Commercial Prospect')], string='Partner Relation')
    planned_revenue = fields.Float(string='Planned Revenue')
    date = fields.Datetime(string='Date', size=16, default=time.strftime('%Y-%m-%d %H:%M:%S'))
    document = fields.Reference([('product.product', 'Product'), ('crm.case', 'Case'), ('account.invoice', 'Invoice'), ('stock.production.lot', 'Production Lot'), ('project.project', 'Project'), ('project.task', 'Project task'), ('purchase.order', 'Purchase Order'), ('sale.order', 'Sale Order')], string='Document', size=128)
    
    @api.one
    def create_event(self): #TODO: Need to ask what to do?
        obj_event = self.env['mail.message']  #replace res.partner.event with mail.message
        partner_ids = self.env.context.get('active_ids')  
        val = {
           'subject' : self.name,
           'partner_ids' : [(6,0,partner_ids)],
           'author_id' :self.user_id.id,
#                'probability' :data['form']['probability'],
#                 'canal_id' :data['form']['canal_id'],
#                'type' :data['form']['type'],
#                'planned_cost' :data['form']['planned_cost'],
           'body' : self.description,
#                'som' :data['form']['som'],
#                'partner_type' :data['form']['partner_type'],
#                'planned_revenue' :data['form']['planned_revenue'],
            'type' : 'notification',
           'date' : self.date,
           'model' : self.document or '',
           'res_id': self.document and self.document.id or ''
               }
        id_event_history = obj_event.create(val)
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
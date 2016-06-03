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

class event_create_registrations(models.TransientModel):
    _name = 'event.create_registrations'
    
    event_id = fields.Many2one('event.event', string='Event', required=True)
    
    @api.multi
    def create_reg_event(self):
        reg_ids = []
        
        event_obj = self.env['event.event']
        registration_obj = self.env['event.registration']
        reg_datas = registration_obj.browse(self.env.context['active_ids'])
        for reg in reg_datas:
            reg.copy({'event_id': self.event_id.id})
        
        self.env.cr.execute('select id from event_registration where event_id = %s' % (self.event_id.id))
        map(lambda x:reg_ids.append(x[0]), self.env.cr.fetchall())
        resource = self.env.ref('event.view_event_registration_form')
        return {
            'domain': "[('id','in', [" + ','.join(map(str, reg_ids)) + "])]",
            'name': 'Registrations',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.registration',
            'views': [(False, 'tree'), (resource.id, 'form')],
            'type': 'ir.actions.act_window'
        }
    
#     @api.multi
#     def _open_reg(self):
#         reg_ids = []
#         self.env.cr.execute('select id from event_registration where event_id = %s' % (self.event_id.id))
#         map(lambda x:reg_ids.append(x[0]), cr.fetchall())
#         resource = self.env.ref('cci_event.event_registration_form')
#         return {
#             'domain': "[('id','in', [" + ','.join(map(str, reg_ids)) + "])]",
#             'name': 'Registrations',
#             'view_type': 'form',
#             'view_mode': 'tree,form',
#             'res_model': 'event.registration',
#             'views': [(False, 'tree'), (resource.id, 'form')],
#             'type': 'ir.actions.act_window'
#         }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
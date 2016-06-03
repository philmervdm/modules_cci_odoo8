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

class event_confirm_registrations(models.TransientModel):
    _name = 'event.confirm.registrations'

    @api.multi
    def confirm_reg(self):
        registration_obj = self.env['event.registration']
        message = ''
#         if self.env.context.get('active_ids', []):
#             reg_datas = registration_obj.browse,(self.env.context['activeids'])
#             ids_case = []
#         for reg in reg_datas:
#             if not reg.check_ids:
#                 ids_case.append(reg.case_id)
        reg_ids = registration_obj.search([('state', '=', 'draft')])
        if not reg_ids:
            message = 'No Draft Registration Available'
            
        reg_ids.write({'state': 'open', })
#         reg_ids._history('Open', history=True)
        reg_ids.mail_user()
        message = 'All Draft Registration confirmed'
        ctx = self.env.context.copy()
        ctx.update({'message': message})
        resource = self.env.ref('cci_event.event_confirm_registrations_msg_view')
        return {
            'name': 'Registrations',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.confirm.registrations.msg',
            'views': [(resource.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
        
class event_confirm_registrations_msg(models.TransientModel):
    _name = 'event.confirm.registrations.msg'
    
    message = fields.Text(string='Message', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(event_confirm_registrations_msg, self).default_get(fields)
        if self.env.context.has_key('message'):
            res.update({'message': self.env.context['message']})
        return res    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
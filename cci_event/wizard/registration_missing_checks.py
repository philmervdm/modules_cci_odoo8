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

from openerp import models, fields, api, _

class cci_event_reg_checks(models.TransientModel):
    _name = 'cci_event.reg.checks'
    
    @api.multi
    def reg_check(self):
        obj_reg = self.env['event.registration']
        regs = obj_reg.search([('check_mode', '=', True)])
#         ids_case = []
#         for i in regs:
#             if not i.check_ids:
#                 ids_case.append(i.case_id)
        model_data = self.env.ref('event.view_event_registration_form')
        return {
            'domain': "[('id','in', [" + ','.join(map(str, regs.ids)) + "])]",
            'name': 'Registration',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.registration',
            'views': [(False, 'tree'), (model_data.id, 'form')],
            'type': 'ir.actions.act_window'
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
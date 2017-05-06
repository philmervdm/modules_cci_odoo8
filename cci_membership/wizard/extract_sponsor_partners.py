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
from openerp import models, fields, api , _


class extract_sponsor_partners(models.TransientModel):
    
    _name = 'extract.sponsor.partners'
    
    only_active = fields.Boolean(string = 'Only active partners')

    @api.multi
    def open_window_selected_partners(self):
        if self.only_active:
            selection = "SELECT id FROM res_partner WHERE active AND state_id = 1 and id in (SELECT distinct(associate_member) from res_partner where associate_member is not null and active)"
        else:
            selection = "SELECT distinct(associate_member) as id FROM res_partner WHERE active AND associate_member is not null"
        
        self.env.cr.execute(selection)
        result_lines = self.env.cr.fetchall()
        partner_ids = [x[0] for x in result_lines]
        result = {
            'domain': [('id', 'in', partner_ids)],
            'name': _('Sponsor Partners'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': { },
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


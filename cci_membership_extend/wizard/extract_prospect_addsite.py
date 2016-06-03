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
from openerp import api, models, _


class extract_prospect_addsite(models.TransientModel):
    _name = 'extract.prospect.addsite'

    @api.multi
    def open_window_selected_partners(self):
        partner_obj = self.env['res.partner']
        members = partner_obj.search([('state_id', '=', 1), ('site_membership', '<', 1),
                                      ('membership_state', 'in', ['free', 'invoiced', 'paid'])])
        partner_ids = []
        for partner in members:
            if partner.address and len(partner.address) > 1:
                partner_ids.append(partner.id)
        result = {
            'domain': [('id', 'in', partner_ids)],
            'name': _('Prospects Additional Site Membership'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

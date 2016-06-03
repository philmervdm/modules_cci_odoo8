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
from openerp import api, fields, models, _


class extract_new_members_since(models.TransientModel):
    _name = 'extract.new.members.since'

    since = fields.Date(string='New Since', required=True)

    @api.multi
    def open_window_selected_partners(self):
        selection = "SELECT id FROM res_partner \
                    WHERE active AND membership_state in ('free','invoiced','paid') \
                    AND cci_date_start_membership >= '%s'" % self.since
        self.env.cr.execute(selection)
        partners = self.env.cr.fetchall()
        partner_ids = [x[0] for x in partners]
        result = {
            'domain': [('id', 'in', partner_ids)],
            'name': _("New Members Since '%s'") % self.since,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

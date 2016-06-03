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


class extract_used_membership_amount(models.TransientModel):

    _name = 'extract.used.membership.amount'

    only_members = fields.Boolean(string='Only for current members', default=True,
                                  help='If not checked, the list will count ALL active partners ...')

    @api.multi
    def open_window_counts(self):
        # delete all old values
        selection = "DELETE FROM cci_membership_membership_askedused"
        self.env.cr.execute(selection)
        selection = ''  # unusefull just for the case of
        # count by grouping
        if self.only_members:
            selection = "SELECT membership_amount, COUNT(id) FROM res_partner WHERE active \
            AND membership_state in ('free','invoiced','paid') \
            AND state_id = 1 GROUP BY membership_amount ORDER BY membership_amount"
            sel_type = 'members'
        else:
            selection = "SELECT membership_amount, COUNT(id) FROM res_partner WHERE active \
            AND state_id = 1 GROUP BY membership_amount ORDER BY membership_amount"
            sel_type = 'all'
        self.env.cr.execute(selection)
        counts = self.env.cr.fetchall()
        m_used_obj = self.env['cci_membership.membership_askedused']
        if counts:
            for line in counts:
                data = {'amount': line[0] or 0.0,
                        'count': line[1] or 0,
                        'total_value': (line[0] or 0.0)*(line[1] or 0),
                        'type': sel_type
                        }
                newcount_id = m_used_obj.create(data)
        result = {
            'name': _('Used Membership Amounts'),
            'view_type': 'form',
            'view_mode': 'tree,graph,form',
            'res_model': 'cci_membership.membership_askedused',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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


class extract_partners_by_amount(models.TransientModel):
    _name = 'extract.partners.by.amount'

    only_members = fields.Boolean(string='Only for current members', default=True,
                                  help='If not checked, the list will count ALL active partners ...')

    @api.multi
    def open_window_selected_partners(self):
        active_ids = self.env.context.get('active_ids')
        amounts = self.env['cci_membership.membership_askedused'].browse(active_ids).read(['amount', 'type'])
        if len(active_ids) > 1:
            var = ','.join([str(x['amount']) for x in amounts])
            if len(var) > 40:
                var_screen = var[0:37]+'...'
        else:
            var_screen = var = str(amounts[0]['amount'])
        if amounts[0]['type'] == 'members':
            screen_name = _('Members with Membership Amounts [%s]') % var_screen
            var2 = "AND membership_state in ('free','invoiced','paid')"
        else:
            screen_name = _('Partners with Membership Amounts [%s]') % var_screen
            var2 = ""
        selection = "SELECT id FROM res_partner \
                    WHERE active AND state_id = 1 AND membership_amount in (%s) %s" % (var, var2)
        self.env.cr.execute(selection)
        partners = self.env.cr.fetchall()
        partner_ids = [x[0] for x in partners]
        result = {
            'domain': [('id', 'in', partner_ids)],
            'name': screen_name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

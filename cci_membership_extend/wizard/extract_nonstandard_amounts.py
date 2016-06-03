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
import datetime
from openerp import api, fields, models, _
from openerp.exceptions import Warning


class extract_nonstandard_amounts(models.TransientModel):

    _name = 'extract.nonstandard.amounts'

    year = fields.Integer(string='Membership Year', required=True, default=datetime.datetime.today().year)
    only_members = fields.Boolean(string='Only for current members', default=True,
                                  help='If not checked, the list will give ALL active partners with non-standard membership...')

    @api.multi
    def open_window_selected_partners(self):
        if not self.year:
            raise Warning(_('Warning !'), _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.year and self.year < 1900:
            raise Warning(_('Warning !'), _('You must give the year of membership concerned; between 1900 and the next year'))
        # get the standard ranges
        mranges_obj = self.env['cci_membership.membership_range']
        mranges = mranges_obj.search([('year','=',self.year)])
        if not mranges:
            raise Warning(_('Warning !'), _('The given membership year has no membership ranges defined'))

        # for each ranges, we check the amount of partners inside this range and
        # collect partners with a different amount
        partner_ids = []
        for mrange in mranges:
            if self.only_members:
                selection = "SELECT id FROM res_partner WHERE active AND state_id = 1 AND employee_nbr >= %s \
                AND employee_nbr <= %s AND membership_amount <> 0.0 AND membership_amount <> %s \
                AND membership_state in ('free', 'invoiced', 'paid')" % (mrange.from_range, mrange.to_range, mrange.amount)
            else:
                selection = "SELECT id FROM res_partner WHERE active AND state_id = 1 AND employee_nbr >= %s \
                AND employee_nbr <= %s AND membership_amount <> 0.0 AND \
                membership_amount <> %s" % (mrange.from_range, mrange.to_range, mrange.amount)

            self.env.cr.execute(selection)
            result_lines = self.env.cr.fetchall()
            current_ids = [x[0] for x in result_lines]
            partner_ids.extend(current_ids)

        result = {
            'domain': [('id', 'in', partner_ids)],
            'name': _('Non-Standard Membership Amounts'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


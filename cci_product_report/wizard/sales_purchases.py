# -*- coding: utf-8 -*-
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


class wizard_sales_purchases(models.TransientModel):
    _name = 'wizard.sales.purchases'
    
    period_from = fields.Many2one('account.period', string = 'From', required = True)
    period_to = fields.Many2one('account.period', string = 'To', required = True)
    type = fields.Selection([('sales','Sales Only'),
                             ('purchases','Purchases Only'),
                             ('all','Sales and Purchases')], required = True)
    
    @api.multi
    def _get_period_ids(self,period_from_id,period_to_id):
        period_obj = self.env['account.period']
        per_from = period_obj.browse(period_from_id)
        per_to = period_obj.browse(period_to_id)
        if per_from.date_start > per_to.date_start:
            perto,per_from = per_from,per_to
        period_ids = period_obj.search([('date_start','>=',per_from.date_start),('date_stop','<=',per_to.date_stop),('special','=',False)])
        return period_ids
    
    @api.multi
    def open_window_selected_move_lines(self, data):
        
        period_from = self.read(['period_from'])[0]['period_from'][0]
        period_to = self.read(['period_to'])[0]['period_to'][0]
        period_ids = self._get_period_ids([period_from],[period_to])
        product_ids = data['active_ids']
        if self.type == 'sales':
            journal_ids = self.env['account.journal'].search([('type','=','sale')])
        elif self.type == 'purchases':
            journal_ids = self.env['account.journal'].search([('type','=','purchase')])
        elif self.type == 'all':
            journal_ids = self.env['account.journal'].search(['|',('type','=','sale'),('type','=','purchase')])
        selection = """SELECT aml.id 
                              FROM account_move_line as aml, account_move as am
                              WHERE aml.move_id = am.id AND am.period_id in (%s) AND aml.product_id in (%s)
                              AND aml.journal_id in (%s) AND aml.state = 'valid' AND am.state = 'posted'
                    """ % (','.join(map(str,period_ids.ids)),','.join(map(str,product_ids)),','.join(map(str,journal_ids.ids)))
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        mline_ids = []
        for lid in res:
            mline_ids.append(lid[0])
        result = {
            'domain': [('id', 'in', mline_ids)],
            'name': _('Account Move Lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

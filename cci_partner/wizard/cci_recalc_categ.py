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

import datetime
from openerp import models, fields, api, _

class cci_recalc_categs(models.TransientModel):
    _name = 'cci.recalc.categs'
    
    excluded_ids = fields.Many2many('account.account', string='Ignored accounts', help='List of accounts to ignore for this turnover calculation')
    addition_ids = fields.Many2many('account.account', string='Additionnal accounts', help='List of accounts not in class 7 to include for this turnover calculation')
    valueA = fields.Integer(string='Value A', required=True)
    valueB = fields.Integer(string='Value B', required=True)
    value1 = fields.Integer(string='Value 1', required=True)
    value2 = fields.Integer(string='Value 2', required=True)
    value3 = fields.Integer(string='Value 3', required=True)
    last_period_id = fields.Many2one('account.period', string='Last Period', required=True)
    
    @api.model
    def default_get(self, fields):
        res = super(cci_recalc_categs, self).default_get(fields)
        today = datetime.date.today()
        year = today.year
        month = today.month
        month -= 1
        if month <= 0:
            month += 12
            year -= 1
        last_month_date = datetime.datetime(year, month, 28).strftime('%Y-%m-%d')
        period_obj = self.env['account.period']
        last_period = period_obj.search([('date_start', '<=', last_month_date), ('date_stop', '>=', last_month_date), ('special', '=', False)], limit=1)
        if 'last_period_id' in fields:
            res.update({'last_period_id': last_period.id})
        return res
    
    @api.multi
    def make_calculation(self):
        partner_obj = self.env['res.partner']
        result_method = partner_obj.calculate_type_customer(
                                                 excluded_accounts=self.excluded_ids.ids,
                                                 additional_accounts=self.addition_ids.ids,
                                                 letters_range=[ self.valueA, self.valueB ],
                                                 digits_range=[ self.value1, self.value2, self.value3 ],
                                                 last_period_id=self.last_period_id.id)
        ctx = self.env.context.copy()
        ctx.update({'result':result_method})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.recalc.categs.result',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }


class wizard_recalc_categs_result(models.TransientModel):
    _name = 'wizard.recalc.categs.result'
    
    result = fields.Text(string='Final Result')
    
    @api.model
    def default_get(self, fields):
        res = super(wizard_recalc_categs_result, self).default_get(fields)
        res.update({'result': self.env.context.get('result', '')})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
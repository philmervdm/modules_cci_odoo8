# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import time
from openerp import api, fields, models, _
    
class cci_analytic_cross_details(models.Model):

    _name='cci.analytic.cross.details'
    _description = "CCI Account Analytic Line Report"

    name = fields.Date(string= 'Date', readonly=True,)
    product_id = fields.Many2one('product.product', string = 'Product', readonly=True,)
    gl_account_id =  fields.Many2one('account.account',string = 'Account', readonly=True,)
    move_id = fields.Many2one('account.move', string = 'Move', readonly=True,)
    partner_id = fields.Many2one('res.partner', string= 'Partner', readonly=True,)
    period_id = fields.Many2one('account.period', string = 'Period', readonly=True,)
    account1_id = fields.Many2one('account.analytic.account', string = 'Account1')
    account2_id = fields.Many2one('account.analytic.account',string = 'Account2')
    account3_id = fields.Many2one('account.analytic.account',string = 'Account3')
    amount1 = fields.Float(string = 'Amount1')
    amount2 = fields.Float(string = 'Amount2')
    amount3 = fields.Float(string = 'Amount3')


class cci_analytic_cross(models.TransientModel):

    _name='cci.analytic.cross'
    
    product_ids =  fields.Many2many('product.product', 'product_analytic', 'product_id', 'analytic_id', string = 'Products')
    date_from = fields.Date(string = 'Date From', default=time.strftime('%Y-01-01'))
    product_null = fields.Boolean(string = 'With no products')
    date_to = fields.Date(string = 'Date To', default=fields.Date.context_today)
    
    @api.multi
    def action_create(self):
        def get_matching_vals(d, mk):
            return sum([k[1] for k, v in d.items() if (k[0], k[2]) == mk])

        def parent_account_id(account_id):
            parent_account = self.env['account.analytic.account'].browse([account_id])[0]
            while parent_account.parent_id.id != False:
                parent_account = self.env['account.analytic.account'].browse([parent_account.parent_id.id])[0]
            return parent_account

        def parent_account_id_id(account_id):
            res = parent_account_id(account_id)
            return res and res.id

        prod_ids = data_ids = []
        date_from=self.date_from
        details_obj = self.env['cci.analytic.cross.details']
        move_l_obj = self.env['account.move.line']
        if not date_from:
            date_from = time.strftime('%Y-01-01')
        date_to=self.date_to
        if not date_to:
            date_to = time.strftime('%Y-12-31')
        self.env.cr.execute("select distinct(product_id) from account_analytic_line where date >= %s and date <= %s",[date_from,date_to])
        res_products = self.env.cr.fetchall()
        is_none = False
        for (product,) in res_products:
            dict_items = {}
            detail_rec = {}
            last_date = ''
            j = 0
            if product is None:
                self.env.cr.execute("select l.move_id,l.date,l.account_id,amount,am.period_id,l.general_account_id,am.id,aml.partner_id from account_analytic_line l inner join account_move_line aml on aml.id=l.move_id inner join account_move am on am.id=aml.move_id where l.date >= %s and l.date <= %s and l.product_id is null group by aml.move_id,l.date,l.account_id,l.move_id,amount,am.period_id,l.general_account_id,am.id,aml.partner_id order by move_id",[date_from,date_to])
            else:
                self.env.cr.execute("select l.move_id,l.date,l.account_id,amount,am.period_id,l.general_account_id,am.id,aml.partner_id from account_analytic_line l inner join account_move_line aml on aml.id=l.move_id inner join account_move am on am.id=aml.move_id where l.date >= %s and l.date <= %s and l.product_id = %s group by aml.move_id,l.date,l.account_id,l.move_id,amount,am.period_id,l.general_account_id,am.id,aml.partner_id order by move_id",[date_from,date_to,product])
            result = self.env.cr.fetchall()
            dic_t = {}
            date_dico = date_dico2 = {}
            list_date = []
            result.sort()
            i_t = 0
            curr_date = ''
            for rec in sorted(result):
                date = rec[1]
                if len(result) > 2:
                    if (result[0][0] == result[1][0]) and (result[0][0] == result[2][0]):
                        dic_t[tuple(result[:3])] = rec[1]
                        len(result) and result.pop(0)
                        len(result) and result.pop(0)
                len(result) and result.pop(0)
                curr_date = rec[1]
            j=0
            tmp_2 = ''
            len_result = len(result)
            i = 0
            data = sorted(dic_t.keys())
            data.sort()
            for rec in data:
                i = 0
                for item in rec:
                    i+=1
                    detail_rec['name'] = item[1]
                    parent_account = parent_account_id(item[2])
                    parent_id = parent_account and parent_account.id
                    detail_rec['product_id'] = product
                    detail_rec['move_id'] = item[6]
                    if not detail_rec.get('partner_id', False) and item[7]:
                        detail_rec['partner_id'] = item[7]
                    detail_rec['period_id'] = item[4]
                    detail_rec['gl_account_id'] = item[5]
                    if parent_id == 1:
                        detail_rec['account1_id'] = item[2]
                        detail_rec['amount1'] = item[3]
                    elif parent_id == 2:
                        detail_rec['account2_id'] = item[2]
                        detail_rec['amount2'] = item[3]
                    elif parent_id == 3:
                        detail_rec['account3_id'] = item[2]
                        detail_rec['amount3'] = item[3]
                    if detail_rec.values() and detail_rec.get('account1_id',None) and detail_rec.get('account2_id',None) and detail_rec.get('account3_id',None) and detail_rec.get('amount1',None) and detail_rec.get('amount2',None) and detail_rec.get('amount3',None):
                        detail_id = details_obj.create(detail_rec)
                        data_ids.append(detail_id)
                        detail_rec = {}
                        i = 0
                i += 1
        return {
                'view_type': 'form',
                'domain': "[('id', 'in', %s)]" % str(data_ids),
                "view_mode": 'tree,form',
                'res_model': 'cci.analytic.cross.details',
                'type': 'ir.actions.act_window',
        }
        return True
cci_analytic_cross()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

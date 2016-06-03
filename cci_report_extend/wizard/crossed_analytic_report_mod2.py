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
from openerp import models, fields, api, _

class cci_analytic_cross_details2(models.Model):

    _name='cci.analytic.cross.details2'
    _description = "CCI Account Analytic Line Report 2012"

    name = fields.Char('Name', size=64, readonly=True, select=True)
    product_id = fields.Many2one('product.product','Product', readonly=True, select=True)
    gl_account_id = fields.Many2one('account.account','Account', readonly=True, select=True)
    move_id = fields.Many2one('account.move','Move', readonly=True, select=True)
    partner_id = fields.Many2one('res.partner','Partner', readonly=True, select=True)
    period_id = fields.Many2one('account.period','Period', readonly=True, select=True)
    account1_id = fields.Many2one('account.analytic.account','Account1')
    account2_id = fields.Many2one('account.analytic.account','Account2')
    amount = fields.Float('Amount')
    
class cci_analytic_cross2(models.TransientModel):

    _name='cci.analytic.cross2'
    
    period_from = fields.Many2one('account.period','Period From')
    period_to = fields.Many2one('account.period','Period To')
    account_id = fields.Many2one('account.account','General Account')
    expand_account_id = fields.Boolean('with sub-accounts')
    analytic_plan_id1 = fields.Many2one('account.analytic.account','Analytic Plan 1')
    analytic_account_id1 = fields.Many2one('account.analytic.account','Analytic Account 1')
    expand_analytic1 = fields.Boolean('with analytic sub-accounts on plan 1')
    analytic_plan_id2 = fields.Many2one('account.analytic.account','Analytic Plan 2')
    analytic_account_id2 = fields.Many2one('account.analytic.account','Analytic Account 2')
    expand_analytic2 = fields.Boolean('with analytic sub-accounts on plan 2')

    @api.multi
    def action_create(self):
        def get_matching_vals(d, mk):
            return sum([k[1] for k, v in d.items() if (k[0], k[2]) == mk])

        def parent_account_id(account_id):
            parent_account = self.env['account.analytic.account'].browse([account_id])[0]
            while parent_account.parent_id.id != False:
                parent_account = self.env['account.analytic.account'].browse([parent_account.parent_id.id])[0]
            return parent_account

        def get_account_descendants(account_id,prev_list):
            account_obj = self.env['account.account']
            prev_list.append(account_id)
            father = account_obj.browse(account_id)
            if father.child_id:
                for sub_account in father.child_id:
                    prev_list = get_account_descendants(sub_account.id, prev_list )
            return prev_list

        def get_analytic_account_descendants(aaccount_id,prev_list):
            account_obj = self.env["account.analytic.account"]
            prev_list.append(aaccount_id)
            father = account_obj.browse(aaccount_id)
            if father.child_ids:
                for sub_account in father.child_ids:
                    prev_list = get_analytic_account_descendants(sub_account.id, prev_list )
            return prev_list

        def parent_account_id_id(account_id):
            res = parent_account_id(account_id)
            return res and res.id

        data_ids = []
        period_from_id = self.period_from.id
        period_to_id = self.period_to.id
        general_account_id = self.account_id.id
        aplan_id1 = self.analytic_plan_id1.id
        aplan_id2 = self.analytic_plan_id2.id
        aaccount_id1 = self.analytic_account_id1.id
        aaccount_id2 = self.analytic_account_id2.id
        expand_general = self.expand_account_id
        expand_analytic1 = self.expand_analytic1
        expand_analytic2 = self.expand_analytic2
        details_obj = self.env['cci.analytic.cross.details2']
        move_l_obj = self.env['account.move.line']

#        selection of all account move line id with the two periods and with selected general account if asked
        period_obj = self.env['account.period']
        per_from = period_obj.browse(period_from_id).read(['id','date_start','date_stop'])[0]
        per_to = period_obj.browse(period_to_id).read(['id','date_start','date_stop'])[0]
        if per_from['date_start'] > per_to['date_start']:
            perto,per_from = per_from,per_to
        
        period_ids = period_obj.search([('date_start','>=',per_from['date_start']),('date_stop','<=',per_to['date_stop']),('special','=',False)])
        if general_account_id:
            if expand_general:
                account_ids = get_account_descendants(general_account_id,[])
            else:
                account_ids = [general_account_id]
            self._cr.execute("select id from account_move_line where period_id in (%s) and account_id in (%s)" % (','.join([str(x) for x in period_ids.ids]),','.join([str(x) for x in account_ids])) )
            lines = self._cr.fetchall()
            general_ids = [x[0] for x in lines]
        else:
            self._cr.execute("select id from account_move_line where period_id in (%s)" % ','.join([str(x) for x in period_ids.ids]) )
            lines = self._cr.fetchall()
            general_ids = [x[0] for x in lines]

#        selection of all account move line id linked to the first analytic account
        if aaccount_id1:
            if expand_analytic1:
                aaccount1_ids = get_analytic_account_descendants(aaccount_id1,[])
            else:
                aaccount1_ids = [aaccount_id1]
            self._cr.execute("select distinct(move_id) from account_analytic_line where account_id in (%s)" % ','.join([str(x) for x in aaccount1_ids]) )
            lines = self._cr.fetchall()
            analytic1_ids = [x[0] for x in lines]
        else:
            analytic1_ids = []

#        selection of all account move line id linked to the second analytic account
        if aaccount_id2:
            if expand_analytic2:
                aaccount2_ids = get_analytic_account_descendants(aaccount_id2,[])
            else:
                aaccount2_ids = [aaccount_id2]
            self._cr.execute("select distinct(move_id) from account_analytic_line where account_id in (%s)" % ','.join([str(x) for x in aaccount2_ids]) )
            lines = self._cr.fetchall()
            analytic2_ids = [x[0] for x in lines]
        else:
            analytic2_ids = []

#        matching between these three possible result sets into a list of unique account_move_line ids
        if aaccount_id1:
            mline_ids = [x for x in set(general_ids).intersection(set(analytic1_ids))]
        else:
            mline_ids = general_ids
        if aaccount_id2:
            mline_ids = [x for x in set(mline_ids).intersection(set(analytic2_ids))]

        if mline_ids:
            account_plan1_ids = get_analytic_account_descendants(aplan_id1,[])
            account_plan2_ids = get_analytic_account_descendants(aplan_id2,[])
            mlines = move_l_obj.browse(mline_ids)
            for mline in mlines:
                detail_rec = {}
                detail_rec['name'] = mline.name or ''
                detail_rec['product_id'] = mline.product_id and mline.product_id.id or False
                detail_rec['gl_account_id'] = mline.account_id.id
                detail_rec['move_id'] = mline.move_id.id
                detail_rec['partner_id'] = mline.partner_id.id
                detail_rec['period_id'] = mline.period_id.id
#                calculation of the repartition of the amount between analytics
#                because the rate of repartition can be different from 100%
                if len(mline['analytic_lines']) == 2:
#                     the rate must be 100% for all lines
                    detail_rec['amount'] = mline['analytic_lines'][0].amount
                    for aline in mline['analytic_lines']:
                        if aline.account_id.id in account_plan1_ids:
                            detail_rec['account1_id'] = aline.account_id.id
                        elif aline.account_id.id in account_plan2_ids:
                            detail_rec['account2_id'] = aline.account_id.id
                    detail_id = details_obj.create(detail_rec)
                    data_ids.append(detail_id)
                else:
#                     there is a rate of repartition between each plans
#                     we create only the lines that correspond to the filter asked by the user
                    count1 = count2 = 0
                    amount1 = amount2 = 0
                    adetails1 = []
                    adetails2 = []
                    for aline in mline['analytic_lines']:
                        if aline.account_id.id in account_plan1_ids:
                            count1 += 1
                            amount1 += aline.amount 
                            adetails1.append([aline.amount,aline.account_id.id])
                        elif aline.account_id.id in account_plan2_ids:
                            count2 += 1
                            amount2 += aline.amount 
                            adetails2.append([aline.amount,aline.account_id.id])
                    if count1 == 1 or count2 == 1:
#                         there is a split only on 1 plan
                        if count1 == 1:
#                             the second plan is split
                            for detail in adetails2:
                                if ( aaccount_id2 and adetails2[0][1] in aaccount2_ids ) or not aaccount_id2:
                                    line_rec = detail_rec
                                    line_rec['amount'] = detail[0]
                                    line_rec['account2_id'] = detail[1]
                                    line_rec['account1_id'] = adetails1[0][1]
                                    detail_id = details_obj.create(line_rec)
                                    data_ids.append(detail_id)
                        else:
#                             the first plan is split
                            for detail in adetails1:
                                if ( aaccount_id1 and adetails1[0][1] in aaccount1_ids ) or not aaccount_id1:
                                    line_rec = detail_rec
                                    line_rec['amount'] = detail[0]
                                    line_rec['account1_id'] = detail[1]
                                    line_rec['account2_id'] = adetails2[0][1]
                                    detail_id = details_obj.create(line_rec)
                                    data_ids.append(detail_id)
                    else:
#                         there is a split on both plans
                        amount_total = amount1
                        cols = []
                        lines = []
                        for detail in adetails1:
                            if amount_total <> 0.0:
                                cols.append( [detail[0]/amount_total,detail[1]] )
                            else:
                                cols.append( [0.0,detail[1]] )
                        for detail in adetails2:
                            if amount_total <> 0.0:
                                lines.append([detail[0]/amount_total,detail[1]] )
                            else:
                                lines.append([0.0,detail[1]] )
                        for line in lines:
                            for col in cols:
                                if ( ( aaccount_id1 and col[1] in aaccount1_ids ) or not aaccount_id1 ) and ( ( aaccount_id2 and line[1] in aaccount2_ids ) or not aaccount_id2 ):
                                    line_rec = detail_rec
                                    line_rec['amount'] = amount_total * col[0] * line[0]
                                    line_rec['account1_id'] = col[1]
                                    line_rec['account2_id'] = line[1]
                                    detail_id = details_obj.create(line_rec)
                                    data_ids.append(detail_id)
        return {
                'view_type': 'form',
                'domain': "[('id', 'in', %s)]" % str(data_ids),
                "view_mode": 'tree',
                'res_model': 'cci.analytic.cross.details2',
                'type': 'ir.actions.act_window',
        }
        
#    @api.multi
#    def action_cancel(self):
#        return {
#                'view_type': 'form',
#                'domain': "[('id', 'in', [])]",
#                "view_mode": 'tree',
#                'res_model': 'cci.analytic.cross.details2',
#                'type': 'ir.actions.act_window',
#        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

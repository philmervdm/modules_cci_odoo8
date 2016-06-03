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

import wizard
import pooler
from tools.translate import _
from osv import fields,osv
import time

_analytic_form = '''<?xml version="1.0"?>
<form string="make your choice">
    <field name="product_id"/>
    <newline/>
    <field name="date_from"/>
    <field name="date_to"/>
</form>'''


_journal_fields = {
    'product_id': {'string':'Product', 'type':'many2many', 'relation':'product.product', 'required':True},
    'date_from': {'string':'Date From', 'type':'date','required':True},
    'date_to': {'string':'Date to', 'type':'date','required':True},
}
class cci_analytic_cross_details(osv.osv):

    _name='cci.analytic.cross.details'
    _description = "CCI Account Analytic Line Report"

    _columns = {
        'name': fields.date('Date', readonly=True, select=True),
        'product_id': fields.many2one('product.product','Product', readonly=True, select=True),
        'account1_id' : fields.many2one('account.analytic.account','Account1'),
        'account2_id' : fields.many2one('account.analytic.account','Account2'),
        'account3_id' : fields.many2one('account.analytic.account','Account3'),
        'amount1': fields.float('Amount1'),
        'amount2': fields.float('Amount2'),
        'amount3': fields.float('Amount3'),
    }
cci_analytic_cross_details()

class cci_analytic_cross(osv.osv_memory):

    _name='cci.analytic.cross'
    _columns = {
        'product_ids': fields.many2many('product.product', 'product_analytic', 'product_id', 'analytic_id', 'Products'),
        'date_from':fields.date('Date From'),
        'product_null':fields.boolean('With no products'),
        'date_to':fields.date('Date To'),
    }
    _defaults = {
        'date_from':lambda *a: time.strftime('%Y-01-01'),
        'date_to':lambda *a: time.strftime('%Y-%m-%d'),
}

    def action_create(self, cr, uid, ids, context=None):
        def parent_account_id(account_id):
            parent_account = self.pool.get("account.analytic.account").browse(cr,uid,[account_id])[0]
            while parent_account.parent_id.id != False:
                parent_account = self.pool.get("account.analytic.account").browse(cr,uid,[parent_account.parent_id.id])[0]
            return parent_account

        prod_ids = data_ids = []
        date_from=self.browse(cr,uid,ids,context)[0].date_from
        details_obj = self.pool.get('cci.analytic.cross.details')
        if not date_from:
            date_from = time.strftime('%Y-01-01')
        date_to=self.browse(cr,uid,ids,context)[0].date_to
        if not date_to:
            date_to = time.strftime('%Y-12-31')
        cross_id = self.browse(cr,uid,ids,context)[0]
        products = cross_id.product_ids
     #   for prod in products:
     #       if prod.id not in prod_ids:
     #           prod_ids.append(prod.id)
        if not products:
            cr.execute("select distinct(product_id) from account_analytic_line")
            res_products = cr.fetchall()
            for (product,) in res_products:
                prod_ids.append(product)
        for product in prod_ids:
            cr.execute("select sum(amount),account_id,date as amount from account_analytic_line where (product_id in (%s) or product_id is null) and date >= '%s' and date <= '%s'  group by date,account_id order by date,account_id "%(product,date_from,date_to))
          #  else:
          #      cr.execute("select sum(amount),account_id,date as amount from account_analytic_line where product_id in (%s) and date >= '%s' and date <= '%s'  group by date,account_id order by date,account_id "%(product,date_from,date_to))
            detail_rec = {}
            dict_items = {}
            last_date = ''
            j = 0
            for i, r in enumerate(cr.fetchall()):
                if j==0:
                    last_date = r[2]
                j+=1
                parent_account = parent_account_id(r[1])
                parent_id = parent_account and parent_account.id
                if (r[2] == last_date):
                    detail_rec['product_id'] = product
                    detail_rec['name'] = r[2]
                    parent_account = parent_account_id(r[1])
                    parent_id = parent_account and parent_account.id
                    if parent_id == 1:
                        detail_rec['account1_id'] = r[1]
                        detail_rec['amount1'] = r[0]
                    elif parent_id == 2:
                        detail_rec['account2_id'] = r[1]
                        detail_rec['amount2'] = r[0]
                    elif parent_id == 3: 
                        detail_rec['account3_id'] = r[1]
                        detail_rec['amount3'] = r[0]
                if j==3:
                    detail_id = details_obj.create(cr, uid, detail_rec)
                    data_ids.append(detail_id)
                    detail_rec={}
                    j=0
                last_date = r[2]
                dict_items[(r[1],r[2])] = 0
        return {
                'view_type': 'form',
                'domain': "[('id', 'in', %s)]" % str(data_ids),
                "view_mode": 'tree',
                'res_model': 'cci.analytic.cross.details',
                'type': 'ir.actions.act_window',
        }

        return True
cci_analytic_cross()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

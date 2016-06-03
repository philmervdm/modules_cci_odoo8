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
from openerp import api, fields, models, _
# form = """<?xml version="1.0"?>
# <form string="Change Product ID">
#     <field name="new_product_id" colspan="4"/>
#     <field name="confirm" colspan="4"/>
#     <label string="Confirm that you want to change all lines with the same product." colspan="4"/>
#     <label string="Usefull only if you have several lines marked for change." colspan="4"/>
#     <label string="BE CAREFULL IF PRODUCT (OLD OR NEW) IS A MEMBERSHIP PRODUCT. WARN THE ADMINISTRATOR." colspan="4"/>
# </form>"""
# 
# fields = {
#     'new_product_id' : {'string':'New Product','type':'many2one','relation':'product.product','required':True},
#     'confirm': {'string':'Confirmation','type':'boolean','default':False},
#    }

class wizard_change_product_id(models.TransientModel):
    def _change_all_lines(self, cr, uid, data, context):
        if data['ids'] and len(data['ids']) == 1 or ( len(data['ids']) > 1 and data['form']['confirm'] ):
            # correct the account_move_line to apply the change later in the account_analytic_line
            correction = "UPDATE account_move_line set product_id = %s where id in (%s)" % ( str(data['form']['new_product_id']), ','.join([str(x) for x in data['ids']]) )
            cr.execute( correction )

            # recording of the asked changes in the CCI Logs
            pool_obj = pooler.get_pool(cr.dbname)
            log_obj = pool_obj.get('cci_logs.line')
            log_obj.create(cr,uid,{'name':'Change Product ID Wizard',
                                   'datetime':datetime.datetime.now(),
                                   'user_id':uid,
                                   'message':'Product ID changed to ID %s for ids [%s]' % ( str(data['form']['new_product_id']), ','.join([str(x) for x in data['ids']]) ),
                                  })
        return {'type':'state','state':'end'}
#     states = {
#         'init': {
#             'actions': [],
#             'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancel'),('change','Change')]},
#         },
#         'change': {
#             'actions': [_change_all_lines],
#             'result' : {'type':'state', 'state':'end'}
#         },
#     }
# wizard_change_product_id("cci_salesman_change_product_id")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

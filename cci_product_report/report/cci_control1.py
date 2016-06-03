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
from openerp.report import report_sxw
from openerp import models, fields, api, _
class cci_product_report_control1(report_sxw.rml_parse):
    @api.v7
    def __init__(self, cr, uid, name, context):
        super(cci_product_report_control1, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'dist_name': self._dist_name,
            'income_details': self._income_details,
            'expense_details': self._expense_details,
            #'lines_g': self._lines_g,
        })
    @api.v7
    def _dist_name(self,product_id):
        result = '-Aucune-'    
        default_obj = self.pool.get('account.analytic.default')
        anadist_obj = self.pool.get('account.analytic.plan.instance')
        def_ids = default_obj.search(self.cr,self.uid,[('product_id','=',product_id)])
        if def_ids:
            default = default_obj.read(self.cr,self.uid,def_ids[0],['analytics_id'])
            if default['analytics_id']:
                anadist = anadist_obj.read(self.cr,self.uid,default['analytics_id'][0],['name'])
                result = anadist['name']
        return result
    @api.v7
    def _income_details(self,product_id):
        result = '-Aucun-'
        prod_obj = self.pool.get('product.product').browse(self.cr,self.uid,product_id)
        if prod_obj.product_tmpl_id.property_account_income.code:
            result = prod_obj.product_tmpl_id.property_account_income.code
            if prod_obj.product_tmpl_id.taxes_id:
                if len(prod_obj.product_tmpl_id.taxes_id) == 1:
                    result += ' (%s)' % prod_obj.product_tmpl_id.taxes_id[0].name
                else:
                    tax_list = '; '.join(x.name for x in prod_obj.product_tmpl_id.taxes_id)
                    result += ' (%s)' % tax_list
        return result
    @api.v7
    def _expense_details(self,product_id):
        result = '-Aucun-'
        prod_obj = self.pool.get('product.product').browse(self.cr,self.uid,product_id)
        if prod_obj.product_tmpl_id.property_account_expense.code:
            result = prod_obj.product_tmpl_id.property_account_expense.code
            if prod_obj.product_tmpl_id.supplier_taxes_id:
                print len(prod_obj.product_tmpl_id.supplier_taxes_id)
                if len(prod_obj.product_tmpl_id.supplier_taxes_id) == 1:
                    result += ' (%s)' % prod_obj.product_tmpl_id.supplier_taxes_id[0].name
                else:
                    tax_list = '; '.join(x.name for x in prod_obj.product_tmpl_id.supplier_taxes_id)
                    result += ' (%s)' % tax_list
        return result

                      
class cci_product(models.AbstractModel):
    _name = 'report.cci_product_report.cci_product_report_control1'
    _inherit = 'report.abstract_report'
    _template = 'cci_product_report.cci_product_report_control1'
    _wrapped_report_class = cci_product_report_control1

  
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


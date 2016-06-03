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
import time
from openerp.report import report_sxw
from openerp import models, api

class cci_count_invoices(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(cci_count_invoices, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_data': self.get_data,
        })

    def get_data(self, data):
        result=[]
        obj_inv=self.pool.get('account.invoice')
        obj_partner=self.pool.get('res.partner')

        states=['draft','proforma','open','paid','cancel','proforma2']
        types=['out_invoice','in_invoice']

        for type in types:
            res={}
            if type=='out_invoice':
                res['type']='Customer Invoice'
            else:
                res['type']='Supplier Invoice'

            for state in states:
                res[state]=0

            for state in states:
                find_ids=obj_inv.search(self.cr,self.uid,[('partner_id','=',data.id),('state','=',state),('type','=',type)])

                if find_ids:
                    res[state] +=len(find_ids)
            res['proforma'] +=res['proforma2']
            result.append(res)
        return result

class cci_product(models.AbstractModel):
    _name = 'report.cci_partner.cci_count_invoice'
    _inherit = 'report.abstract_report'
    _template = 'cci_partner.cci_count_invoice'
    _wrapped_report_class = cci_count_invoices

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
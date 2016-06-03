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
import datetime
from openerp.osv import osv
from openerp.report import report_sxw

class sheet_281_50(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(sheet_281_50, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time' : time,
            'get_datas' : self._get_datas
        })

    def _get_datas(self, objects):
        record_ids = [x.id for x in objects]
        res_company_id = self.pool.get('res.company').search(self.cr,self.uid,[])[0]
        company_partner_id = self.pool.get('res.company').read(self.cr,self.uid,[res_company_id],['partner_id'])[0]['partner_id'][0]
        company = self.pool.get('res.partner').browse(self.cr,self.uid,company_partner_id)
        record28150_obj = self.pool.get('account.partner281_50')
        records = record28150_obj.browse(self.cr,self.uid,record_ids)
        datas = []
        sequence = 1
        for rec in records:
            data = {}
            data['sequence'] = str(sequence)
            data['year'] = rec.year
            data['issuing_company'] = company.name
            data['issuing_street1'] = company.street or ''
            data['issuing_street2'] = company.street2 or ''
            data['issuing_zip_code'] = company.zip_id and company.zip_id.name or ''
            data['issuing_city'] = company.zip_id and company.zip_id.city or ''
            data['issuing_vat'] = company.vat[2:] if company.vat else ''
            data['company_name'] = rec.name or ''
            data['company_street1'] = rec.street1 or ''
            data['company_street2'] = rec.street2 or ''
            data['company_zip_code'] = rec.zip_code or ''
            data['company_city'] = rec.city or ''
            data['company_vat'] = rec.company_number and rec.company_number[2:] or ''
            data['profession'] = rec.profession or ''
            data['national_number'] = rec.national_number or ''
            data['sum_b'] = ('%.2f' % ( rec.manual_sum_b or rec.calc_sum_b or 0.0 )).replace('.',',')
            data['sum_e'] = ('%.2f' % ( rec.calc_sum_e )).replace('.',',')
            record28150_obj.write(self.cr,self.uid,[rec.id],{'final_sequence':sequence})
            sequence += 1
            datas.append(data)
        record28150_obj.write(self.cr,self.uid,record_ids,{'final_output':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        return datas

class report_sheet_281_50(osv.AbstractModel):
    _name = 'report.cci_account_281_50.report_sheet_281_50'
    _inherit = 'report.abstract_report'
    _template = 'cci_account_281_50.report_sheet_281_50'
    _wrapped_report_class = sheet_281_50

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


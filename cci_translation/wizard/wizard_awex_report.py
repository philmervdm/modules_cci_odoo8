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
from openerp import models, fields, api, _

class translation_awex_report(models.TransientModel):
    _name = 'translation.awex.report'
    
    date_from = fields.Date(string='From Date', required=True, default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To Date', required=True, default=time.strftime('%Y-%m-%d'))
    
    @api.multi    
    def open(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        print "SSS", datas

        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'cci_translation.report_translation_awex',
            'datas': datas
       }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
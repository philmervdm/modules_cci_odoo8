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
from openerp import models, fields , api, _

class check_total(models.TransientModel):
    _name = 'wizard.check.total'

    start_date = fields.Date(string = 'Date1', required = True)
    end_date = fields.Date(string = 'Date2', required = True)
    
    @api.multi
    def print_report(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        
        res.update(datas)
        datas['form'] = res
        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'cci_membership.report_total_sold',
            'datas' : datas
       }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

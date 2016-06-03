# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

from openerp import models, fields , api , _

class cust_status(models.TransientModel):
    
    _name = 'cust.status'
    
    type = fields.Selection([('receivable','Customer - Sales'),('payable','Supplier - Purchases')],required=True,default='receivable')
    only_open = fields.Boolean('Only Open Lines')
    
    @api.multi
    def print_report(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        partners = self.env['res.partner'].browse(self.env.context.get('active_ids',[])).ids
        res = self.read([])
        res = res and res[0] or {}
        res.update({'partner':partners})
        datas['form'] = res
        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'ccih_customer_status.ccih_customer',
            'datas' : datas
       }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

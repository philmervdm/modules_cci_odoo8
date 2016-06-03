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
from openerp import models, fields , api , _
from openerp.exceptions import Warning
import time
import datetime

class select_invoices_by_year(models.TransientModel):
    _name = 'select.invoices.by.year'
    
    year = fields.Integer(string = 'Year of membership', default=datetime.datetime.today().year, required= True)
    select = fields.Selection(string='Type of invoice', default='invoice' , selection=[('all','Invoices and Refunds'),('invoice','Invoices only'),('refund','Refunds only')])

    @api.multi
    def open_window_selected_invoices(self):
        if self.year < 1900 or self.year > datetime.datetime.today().year + 2:
            raise Warning('Warning','You must give the year of membership searched; between 1900 and the next year')

        if self.select == 'refund':
            sel_types = " = 'out_refund'"
        elif  self.select == 'invoice':
            sel_types = " = 'out_invoice'"
        else:
            sel_types = " in ('out_invoice','out_refund')"
            
        selection = "select distinct(ainv.id) from account_invoice as ainv, account_invoice_line as ail, product_product as pp , product_template as pt where pt.membership and pt.membership_year = " + str(self.year) + " and pp.product_tmpl_id = pp.id and ail.product_id = pp.id and ainv.id = ail.invoice_id and ainv.type " + sel_types
        self.env.cr.execute( selection )
        result_lines = self.env.cr.fetchall()
        inv_ids = [x[0] for x in result_lines]

        result = {
            'domain': [('id', 'in', inv_ids)],
            'name': 'Membership Invoices of ' + str(self.year),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'context': { },
            'type': 'ir.actions.act_window'
        }
        return result
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


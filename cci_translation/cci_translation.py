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

class credit_line(models.Model):
    _name = 'credit.line'
    _description = 'Credit line'
    
    @api.model
    def get_available_amount(self, base_amount, partner_id):
        # sum the eligible amounts for translation folder + embassy folder line for everyone and for this partner
        tot_sum = 0
        partner_sum = 0

        # translation folder
        list = self.env['translation.folder'].search([('credit_line_id', '=', self.id), ('state', '<>', 'cancel')])
        for item in list:
            # for everyone
            tot_sum += item.awex_amount
            if item.partner_id.id == partner_id:
                # for this partner
                partner_sum += item.awex_amount

#         # embassy folder line 
        list2 = self.env['cci_missions.embassy_folder_line'].search([('credit_line_id', '=', self.id), ('awex_eligible', '=', True)])
        for item2 in list2:
            # for everyone
            tot_sum += item2.awex_amount
            if item2.folder_id.crm_case_id.partner_id.id == partner_id:
                # for this partner
                partner_sum += item2.awex_amount

        partner_remaining_amount = self.customer_credit - partner_sum
        tot_remaining_amount = self.global_credit - tot_sum

        res = min(base_amount / 2, partner_remaining_amount, tot_remaining_amount)
        if res < 0:
            return 0
        return res

    name = fields.Char('Name', size=32, required=True)
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    global_credit = fields.Float('Global Credit', required=True)
    customer_credit = fields.Float('Customer Max Credit', required=True)

class translation_folder(models.Model):
    _name = 'translation.folder'
    _description = 'Translation Folder'
    
    @api.multi
    def cci_translation_folder_confirmed(self):
        for id in self:
            data = {}
            data['state'] = 'confirmed'
            if id.awex_eligible and id.partner_id.awex_eligible == 'yes':
                # look for an existing credit line in the current time
                credit_line = self.env['credit.line'].search([('from_date', '<=', id.order_date), ('to_date', '>=', id.order_date)], limit=1) 
                # credit_line = self.pool.get('credit.line').search(cr, uid, [('from_date','<=',time.strftime('%Y-%m-%d')), ('to_date', '>=', time.strftime('%Y-%m-%d'))])
                if credit_line:
                    # if there is one available: get available amount from it
                    amount = credit_line.get_available_amount(id.base_amount, id.partner_id.id)
                    if amount > 0:
                        data['awex_amount'] = amount
                        data['credit_line_id'] = credit_line[0].id
                    else:
                        data['awex_eligible'] = False
            id.write(data)
        return True

    order_desc = fields.Char('Description', size=64, required=True, index=True, default=lambda self: self.env['ir.sequence'].get('translation.folder'))
    name = fields.Text('Name', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    base_amount = fields.Float('Base Amount', required=True, readonly=True, states={'draft':[('readonly', False)]})
    awex_eligible = fields.Boolean('AWEX Eligible', readonly=True, states={'draft':[('readonly', False)]})
    awex_amount = fields.Float('AWEX Amount', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('invoiced', 'Invoiced'), ('done', 'Done'), ('cancel', 'Cancel')], 'State', readonly=True, default='draft')
    credit_line_id = fields.Many2one('credit.line', 'Credit Line', readonly=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    purchase_order = fields.Many2one('purchase.order', 'Purchase Order')
    order_date = fields.Date('Order Date', required=True, default=time.strftime('%Y-%m-%d'))
    
class letter_credence(models.Model):
    _name = 'letter.credence'
    _description = 'Letter of Credence'

    emission_date = fields.Date('Emission Date', required=True)
    asked_amount = fields.Float('Asked Amount', required=True)

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner'
    
    awex_eligible = fields.Selection([('unknown', 'Unknown'), ('yes', 'Yes'), ('no', 'No')], "AWEX Eligible", default='unknown')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
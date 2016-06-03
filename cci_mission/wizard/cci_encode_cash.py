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

class receive_encode_cash(models.TransientModel):
    _name = 'receive.encode.cash'
    
    journal = fields.Many2one('account.journal', string = 'Cash Type', required = True, domain = "[('type', '=', 'cash')]")
    
    @api.multi
    def next(self):
        ctx = self.env.context.copy()
        ctx['journal'] = self.journal.id
            
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'receive.encode.cash.next',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
        
class receive_encode_cash_next(models.TransientModel):
    _name = 'receive.encode.cash.next'
    
    amt = fields.Float(string = 'Amount', required = True)
    ref =  fields.Char(string = 'Reference', required = True)
    
    @api.model
    def default_get(self,fields):
        res = super(receive_encode_cash_next,self).default_get(fields)
        journal = self.env['account.journal'].browse(self.env.context.get('journal'))
        seq = self.env['ir.sequence'].get(journal.sequence_id.code)
        res.update({'ref' : seq})
        return res
    
    @api.multi
    def rec_enc_cash(self):
        pool_link_statement = self.env['account.bank.statement']
        statement_ids = pool_link_statement.search([('date','=',time.strftime('%Y-%m-%d')),('state','=','draft')])
        message='Your Cash Entries Have Been Encoded to Bank Statement '
        vals={}
        obj_current_model = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids')) #pool_link.get(data['model']).browse(cr,uid,data['ids'])
    
        statements_lines=[]
    
        for item in obj_current_model:
            res={}
            res['name'] = item.name
            res['ref'] = self.ref
            res['amount'] = self.amt
            
            if 'order_partner_id' in item:
                res['partner_id'] = item.order_partner_id.id
                if not res['partner_id']:
                    raise Warning(_('Warning'), _('No Partner Defined on Embassy folder'))
#                 data_account = self.env['account.bank.statement.line'].onchange_partner_id(line_id=[],partner_id=item.order_partner_id.id,type='general',currency_id=False)
            else:
                res['partner_id'] = item.partner_id.id
                if not res['partner_id']:
                    raise Warning(_('Warning'), _('No Partner Defined on Embassy folder'))
#                 data_account = self.env['account.bank.statement.line'].onchange_partner_id(line_id=[],partner_id=item.partner_id.id,type='general',currency_id=False)
            
#             res['account_id'] = data_account['value']['account_id']
            statements_lines.append([0,0,res])
    
        vals['line_ids'] = statements_lines
    
        if statement_ids:
            statement_ids[0].write(vals)
            message += statement_ids[0].name
        else:
            vals['journal_id'] = self.env.context.get('journal')
            statement_id = pool_link_statement.create(vals)
            message += statement_id.name
    
        ctx = self.env.context.copy()
        ctx['msg'] = message
        
        return {
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'receive.encode.cash.notify',
        'view_id': False,
        'type': 'ir.actions.act_window',
        'target': 'new',
        'context': ctx,
    }
        
        return data['form']


class receive_encode_cash_notify(models.TransientModel):
    _name= 'receive.encode.cash.notify'
     
    message = fields.Text(string='', readonly = True)
 
    @api.model
    def default_get(self,fields):
        res = super(receive_encode_cash_notify,self).default_get(fields)
        res.update({'message' : self.env.context.get('msg')})
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

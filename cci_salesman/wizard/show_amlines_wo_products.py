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
from openerp import api, fields, models, _
import datetime

def _show_amlines_woprod(self, cr, uid, data, context):
    obj_journal = pooler.get_pool(cr.dbname).get('account.journal')
    journal_ids = obj_journal.search(cr,uid,[('type','=','sale')])
    obj_account_type = pooler.get_pool(cr.dbname).get('account.account.type')
    type_ids = obj_account_type.search(cr,uid,[('code','=','income')])
    obj_account = pooler.get_pool(cr.dbname).get('account.account')
    account_ids = obj_account.search(cr,uid,[('user_type','in',type_ids)])
    value = {
        'domain': [('journal_id','in',journal_ids),('product_id','=',False),('account_id','in',account_ids),('date','>=','2012-01-01')],
        'name': 'Move Lines wo Product',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'account.move.line',
        'context': {},
        'type': 'ir.actions.act_window'
    }
    return value

class extract_amlines_wo_products(models.TransientModel):
    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'action',
                'action': _show_amlines_woprod,
                'state': 'end'
            }
        },
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


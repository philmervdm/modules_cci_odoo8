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
from openerp.report import report_sxw
from openerp import models, api

class ccih_customer_status(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ccih_customer_status, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'get_lines': self._get_lines,
            'sum_debit': self._get_sum_debit,
            'sum_credit': self._get_sum_credit,
            'balance': self._get_balance,
            'get_title': self._get_title,
            'get_coord': self._get_coordinates,
            'get_customer_coordinates': self._get_customer_coordinates,
        })

    def _get_lines(self, form):
        result = []
        objects = self.pool.get('res.partner').browse(self.cr,self.uid,form['partner'][0])
        account_obj = self.pool.get('account.account')
        account_ids = account_obj.search(self.cr,self.uid,[('type','=',form['type'])])
        if account_ids:
            period_obj = self.pool.get('account.period')
            period_ids = period_obj.search(self.cr,self.uid,[('special','=',False)])
            partner_id = objects[0].id
            mline_obj = self.pool.get('account.move.line')
            if form['only_open']:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid'),('reconcile_id','=',False)])
            else:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid')])
            if mline_ids:
                mlines = mline_obj.browse(self.cr,self.uid,mline_ids)
                for mline in mlines:
                    record = {}
                    record['move_name'] = mline.move_id and mline.move_id.name or '-'
                    record['journal'] = mline.journal_id and mline.journal_id.code or '-'
                    record['date'] = mline.date[8:10]+'/'+mline.date[5:7]+'/'+mline.date[0:4]
                    record['period'] = mline.period_id.name
                    record['debit'] = '%.2f' % (mline.debit or 0.0)
                    record['credit'] = '%.2f' % (mline.credit or 0.0)
                    record['reconcile'] = mline.reconcile_id and mline.reconcile_id.name or ''
                    result.append(record)
        return result

    def _get_sum_debit(self, form):
        result = 0.0
        objects = self.pool.get('res.partner').browse(self.cr,self.uid,form['partner'][0])
        account_obj = self.pool.get('account.account')
        account_ids = account_obj.search(self.cr,self.uid,[('type','=',form['type'])])
        if account_ids:
            period_obj = self.pool.get('account.period')
            period_ids = period_obj.search(self.cr,self.uid,[('special','=',False)])
            partner_id = objects[0].id
            mline_obj = self.pool.get('account.move.line')
            if form['only_open']:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid'),('reconcile_id','=',False)])
            else:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid')])
            if mline_ids:
                mlines = mline_obj.browse(self.cr,self.uid,mline_ids)
                for mline in mlines:
                    result += mline.debit or 0.0
        return '%.2f' % result

    def _get_sum_credit(self, form):
        result = 0.0
        result = 0.0
        objects = self.pool.get('res.partner').browse(self.cr,self.uid,form['partner'][0])
        account_obj = self.pool.get('account.account')
        account_ids = account_obj.search(self.cr,self.uid,[('type','=',form['type'])])
        if account_ids:
            period_obj = self.pool.get('account.period')
            period_ids = period_obj.search(self.cr,self.uid,[('special','=',False)])
            partner_id = objects[0].id
            mline_obj = self.pool.get('account.move.line')
            if form['only_open']:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid'),('reconcile_id','=',False)])
            else:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid')])
            if mline_ids:
                mlines = mline_obj.browse(self.cr,self.uid,mline_ids)
                for mline in mlines:
                    result += mline.credit or 0.0
        return '%.2f' % result

    def _get_balance(self, form):
        result = 0.0
        result = 0.0
        objects = self.pool.get('res.partner').browse(self.cr,self.uid,form['partner'][0])
        account_obj = self.pool.get('account.account')
        account_ids = account_obj.search(self.cr,self.uid,[('type','=',form['type'])])
        if account_ids:
            period_obj = self.pool.get('account.period')
            period_ids = period_obj.search(self.cr,self.uid,[('special','=',False)])
            partner_id = objects[0].id
            mline_obj = self.pool.get('account.move.line')
            if form['only_open']:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid'),('reconcile_id','=',False)])
            else:
                mline_ids = mline_obj.search(self.cr,self.uid,[('account_id','in',account_ids),('partner_id','=',partner_id),('period_id','in',period_ids),('state','=','valid')])
            if mline_ids:
                mlines = mline_obj.browse(self.cr,self.uid,mline_ids)
                for mline in mlines:
                    result += (( mline.debit or 0.0 ) - (mline.credit or 0.0))
        return '%.2f' % result

    def _get_title(self, form):
        objects = self.pool.get('res.partner').browse(self.cr,self.uid,form['partner'][0])
        result = 'Etat de compte ' + ( form['type'] == 'receivable' and 'Client' or 'Fournisseur' )
        result += ( '\n' + objects[0].name + ' [%s]' % str(objects[0].id) )
        return result

    def _get_customer_coordinates(self, form):
        objects = self.pool.get('res.partner').browse(self.cr,self.uid,form['partner'][0])
        partner_id = objects[0].id
        partner = self.pool.get('res.partner').browse(self.cr,self.uid,partner_id)
        # search for invoice address, else default address, else first address
        current_address_type = ''
        current_address = False
        for address in partner.child_ids:
            if address.type == 'invoice':
                current_address_type == 'invoice'
                current_address = address
                break
            elif address.type == 'default':
                if current_address_type != 'invoice':
                    current_address_type = 'default'
                    current_address = address
            elif address.type == 'other':
                if not current_address_type:
                    current_address_type = 'other'
                    current_address = address
        if not current_address_type:
            result = partner.name + '\nAucune adresse connue\n!!!!!!'
        else:
            result  = partner.name + '\n' + (current_address.street or '')
            if current_address.street2:
                result += '\n' + (current_address.street2 or '')
            if current_address.zip_id:
                result += '\n' + current_address.zip_id.name + ' ' + current_address.zip_id.city
            if current_address.country_id:
                result += '\n' + current_address.country_id.name
        if partner.vat_subjected:
            if partner.vat:
                if partner.vat[0:2] == 'BE':
                    result += '\n-\nTVA : BE-' + partner.vat[2:6]+'.'+partner.vat[6:9]+'.'+partner.vat[9:12]
                else:
                    result += '\n-\nTVA : ' + partner.vat
            else:
                result += '\n-\nTVA : inconnue (à nous communiquer SVP)'
        else:
            result += '\n-\nTVA : Non-assujetti'
        return result

    def _get_coordinates(self, form, objects):
        result = ''
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(self.cr,self.uid,[self.uid])[0]
        result = user.name
        if user.phone:
            result += u' - Tél : ' + user.phone
        if user.fax:
            result += u' - Fax : ' + user.fax
        if user.email:
            result += u' - Courriel : ' + user.email
        return result

class cci_product(models.AbstractModel):
    _name = 'report.ccih_customer_status.ccih_customer'
    _inherit = 'report.abstract_report'
    _template = 'ccih_customer_status.ccih_customer'
    _wrapped_report_class = ccih_customer_status
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


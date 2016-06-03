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

class one2many_mod_advert(fields.One2many):
#this class is used to display crm.case with fields ref or ref2 which are related to the current object
    
    @api.v7
    def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
        if not context:
            context = {}
        if not values:
                values = {}
        res = {}
        for id in ids:
            res[id] = []
        for id in ids:
            temp = 'sale.order,'+str(id)
            query = "select id from crm_lead where ref = '%s' or ref2 = '%s'" %(temp,temp)
            cr.execute(query)
            case_ids = [ x[0] for x in cr.fetchall()]
            ids2 = obj.pool.get('crm.lead').search(cr, user, [(self._fields_id,'in',case_ids)], limit=self._limit)
            for r in obj.pool.get(self._obj).read(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
                res[id].append( r['id'] )
        return res


class sale_order(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"
    
    case_ids =  one2many_mod_advert('crm.lead', 'id', "Related Cases")
    parent_so = fields.Many2one('sale.order', string = 'Parent Sales Order')
    child_so = fields.One2many('sale.order','parent_so', string = 'Child Sales Order')
    internal_notes = fields.Text(string = 'Internal Note')
    deadline =  fields.Date(string = 'Deadline')
    
    @api.multi
    def onchange_partner_id(self, part):
        warning = False
        data = super(sale_order,self).onchange_partner_id(part)
        if part:
            data_partner = self.env['res.partner'].browse(part)
            if data_partner.alert_others:
                warning = {
                    'title': "Warning:",
                    'message': data_partner.alert_explanation or 'Partner is not valid'
                        }
        if warning:
            data['warning'] =  warning
        return data
    
    @api.v7
    def _make_invoice(self, cr, uid, order, lines, context={}):
        a = order.partner_id.property_account_receivable.id
        if order.payment_term:
            pay_term = order.payment_term.id
        else:
            pay_term = False
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',):
                for preline in preinv.invoice_line:
                    inv_line_id = self.pool.get('account.invoice.line').copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        inv = {
            #'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
#            'reference': "P%dSO%d" % (order.partner_id.id, order.id),
            'account_id': a,
            'partner_id': order.partner_id.id,
#             'address_invoice_id': order.partner_invoice_id.id,
#             'address_contact_id': order.partner_order_id.id,
            'invoice_line': [(6, 0, lines)],
            'user_id': order.user_id and order.user_id.id or False,
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.partner_id.property_account_position.id,
            'comment':order.internal_notes
        }
        inv_obj = self.pool.get('account.invoice')
        inv.update(self._inv_get(cr, uid, order))
        inv_id = inv_obj.create(cr, uid, inv)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id

    
    @api.multi
    def onchange_published_customer(self,published_customer):
        warning  = False
        data = super(sale_order,self).onchange_published_customer(published_customer)
        if published_customer:
            data_partner = self.env['res.partner'].browse(published_customer)
            if data_partner.alert_advertising:
                warning = {
                    'title': "Warning:",
                    'message': data_partner.alert_explanation or 'Partner is not valid'
                        }
        if warning:
            data['warning'] =  warning
        return data

    @api.multi
    def onchange_advertising_agency(self,ad_agency):
        warning  = False
        data = super(sale_order,self).onchange_advertising_agency(ad_agency)
        if ad_agency:
            data_partner = self.env['res.partner'].browse(ad_agency)
            if data_partner.alert_advertising:
                warning = {
                    'title': "Warning:",
                    'message': data_partner.alert_explanation or 'Partner is not valid'
                        }
        if warning:
            data['warning'] =  warning
        return data
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


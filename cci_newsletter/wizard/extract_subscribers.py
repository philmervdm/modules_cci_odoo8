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
# Version 1.0 Philmer
# Created to export also the 250 first caracters of 'comments' fields in Excel format
import time
import datetime
# import re
import base64
from xlwt import *
from openerp.addons.cci_newsletter import cci_newsletter
from openerp import models, fields, api, _
from openerp import tools

class wizard_extract_subscriber(models.TransientModel):
    _name = 'wizard.extract.subscriber'
    
    source_id = fields.Many2one('cci_newsletter.source', string='Source', help='Let this field empty to extract ALL sources')
    
    @api.multi
    def get_file(self):
        obj_subscriber = self.env['cci_newsletter.subscriber']

        # select all subscribers based or not on source
        if self.source_id:
            subs = obj_subscriber.search([('source_id', '=', self.source_id.id)])
        else:
            subs = obj_subscriber.search([])
        if subs:
            subscribers = subs.read(['id', 'internal_id', 'source_id', 'name', 'first_name', 'forced_area', 'email', 'company_name', 'login_name', 'password', 'token', 'comments', 'expire'])
        else:
            subscribers = []

        wb1 = Workbook()
        ws1 = wb1.add_sheet('Inscrits')
        ws1.write(0, 0, 'id')
        ws1.write(0, 1, 'internal_id')
        ws1.write(0, 2, 'source')
        ws1.write(0, 3, 'name')
        ws1.write(0, 4, 'first_name')
        ws1.write(0, 5, 'forced_area')
        ws1.write(0, 6, 'email')
        ws1.write(0, 7, 'company_name')
        ws1.write(0, 8, 'login_name')
        ws1.write(0, 9, 'password')
        ws1.write(0, 10, 'token')
        ws1.write(0, 11, 'comments [250 carac]')
        ws1.write(0, 12, 'expire')
        dAreas = {}
        for area in cci_newsletter.AREAS:
            dAreas[area[0]] = area[1]
        line = 1
        for sub in subscribers:
            ws1.write(line, 0, sub['id'])
            ws1.write(line, 1, sub['internal_id'])
            ws1.write(line, 2, sub['source_id'] and sub['source_id'][1] or '')
            ws1.write(line, 3, sub['name'] or '')
            ws1.write(line, 4, sub['first_name'] or '')
            ws1.write(line, 5, sub['forced_area'] and dAreas[sub['forced_area']].decode('utf-8') or '')
            ws1.write(line, 6, sub['email'] or '')
            ws1.write(line, 7, sub['company_name'] or '')
            ws1.write(line, 8, sub['login_name'] or '')
            ws1.write(line, 9, sub['password'] or '')
            ws1.write(line, 10, sub['token'] or '')
            ws1.write(line, 11, (sub['comments'] or '')[:250])
            ws1.write(line, 12, sub['expire'] and (sub['expire'][8:10] + '/' + sub['expire'][5:7] + '/' + sub['expire'][0:4]) or '')
            line += 1
        wb1.save('subscribers.xls')
        result_file = open('subscribers.xls', 'rb').read()
        
        ctx = self.env.context.copy()
        # give the result tos the user
        ctx.update({'name': 'subscribers.xls', 'msg': _('Save the File with '".xls"' extension.'), 'data': base64.encodestring(result_file)})
        
        view = self.env.ref('cci_newsletter.view_wizard_extract_subscriber_msg_form')
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.subscriber.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class wizard_extract_subscriber_msg(models.TransientModel):
    _name = 'wizard.extract.subscriber.msg'
    
    name = fields.Char(string='Name')
    msg = fields.Text(string='File created', readonly=True)
    subscribers_xls = fields.Binary(string='Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(wizard_extract_subscriber_msg, self).default_get(fields)
        if self.env.context.get('name'):
            rec['name'] = self.env.context['name']
        if self.env.context.get('data'):
            rec['subscribers_xls'] = self.env.context['data']
        if self.env.context.get('msg'):
            rec['msg'] = self.env.context['msg']
        return rec
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

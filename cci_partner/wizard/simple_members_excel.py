# -*- coding: utf-8 -*-
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

import datetime
import base64
from openerp import models, fields, api, _

class wizard_export_simple_members(models.TransientModel):
    _name = 'wizard.export.simple.members'
    
    ftp = fields.Boolean(string='Send by FTP')
    category_id = fields.Many2one('res.partner.category', string='Activity Sector Parent Category')
    
    @api.multi
    def create_and_send(self):
        # use shared method
        partner_obj = self.env['res.partner']
        result_method = partner_obj.export_members_excel(self.category_id.id, self.ftp)
        # re-open result file
        result_file = open('repertoire_des_membres_excel.xls', 'rb').read()
        # give the result to the user
        msg = 'Save the File with '".xls"' extension.'
        repertoire_des_membres_excel = base64.encodestring(result_file)
        
        view = self.env.ref('cci_partner.wizard_export_simple_members_msg_form')
        ctx = self.env.context.copy()
        ctx.update({'name': 'repertoire_des_membres_excel.xls', 'msg': msg, 'data': repertoire_des_membres_excel})
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.export.simple.members.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class wizard_export_simple_members_msg(models.TransientModel):
    _name = 'wizard.export.simple.members.msg'
    
    name = fields.Char(string='Name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    repertoire_des_membres_excel = fields.Binary(string='Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(wizard_export_simple_members_msg, self).default_get(fields)
        if self.env.context.get('name'):
            res.update({'name': self.env.context['name']})
        if self.env.context.get('msg'):
            res.update({'msg': self.env.context['msg']})
        if self.env.context.get('data'):
            res.update({'repertoire_des_membres_excel': self.env.context['data']})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
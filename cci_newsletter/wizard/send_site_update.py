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
import datetime
from openerp import models, fields, api, _

class send_site_update(models.TransientModel):
    _name = 'send.site.update'
    
    connection_id = fields.Many2one('ir.config_parameter', string='Main FTP Connection')
    connection2_id = fields.Many2one('ir.config_parameter', string='Alter Ego Connection')
    ftp_sending = fields.Boolean(string='Sending via FTP')
    login_send = fields.Boolean(string='Sending waitiong new login')
    create_new_login = fields.Boolean(string='Create New Login')
    include_prospects = fields.Boolean(string='Include Prospects')
    include_all_others = fields.Boolean(string='Include all Others eMails')
        
    @api.multi
    def extract_data(self):
        # use shared method
        cci_newsletter_subscriber_obj = self.env['cci_newsletter.subscriber']
        connection_csv = None
        connection_ae = None
        ftp_connection_obj = self.env['ftp_connection']
        if self.connection_id:
            code_csv = self.connection_id.read(['key'])
        if self.connection2_id:
            code_ae = self.connection2_id.read(['key'])

        (result_text, result_count) = cci_newsletter_subscriber_obj.extract_data(code_csv['key'], code_ae['key'], selfftp_sending, self.login_send, self.create_new_login, self.include_prospects, self.include_all_others)
        
        ctx = self.env.context.copy()
        # give the result to the user
        ctx.update({'final_text': result_text, 'final_count': result_count})
        
        view = self.env.ref('cci_newsletter.view_send_site_update_final_form')
        return {
            'name': _('Results'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.site.update.final',
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class send_site_update_final(models.TransientModel):
    _name = 'send.site.update.final'
    
    final_text = fields.Text(string='Changes', readonly=True, default='-')
    final_count = fields.Integer(string='Count', readonly=True, default='-1')
    
    @api.model
    def default_get(self, fields):
        rec = super(send_site_update_final, self).default_get(fields)
        if self.env.context.get('final_text'):
            rec['final_text'] = self.env.context['final_text']
        if self.env.context.get('final_count'):
            rec['final_count'] = self.env.context['final_count']
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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
import datetime
from openerp import tools
from openerp import models, fields, api, _

class cci_memberdirectory_send_email(models.TransientModel):
    _name = 'cci.memberdirectory.send.email'
    
    year = fields.Integer(string='Year', required=True)
    email_from = fields.Char(string='Email From', size=200, required=True)
    title = fields.Char(string='Title', size=200, required=True)
    type = fields.Selection(selection=[('initial', 'Initial Sending'), ('1followup', 'First Follow-Up')], string='Type', required=True)
    
    @api.multi
    def send_emails(self):
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['DirMemberTemplateID', 'DirMemberOptionalID', 'DirMemberOptionalItemID'])
        if param_values.has_key('DirMemberTemplateID') and param_values.has_key('DirMemberOptionalID') and param_values.has_key('DirMemberOptionalItemID'):
            template_obj = self.env['cci_email_template']
            template = template_obj.browse(cr, uid, [param_values['DirMemberTemplateID']])[0]
            add_message = template_obj.browse(cr, uid, [param_values['DirMemberOptionalID']])[0].body
            base_item = template_obj.browse(cr, uid, [param_values['DirMemberOptionalItemID']])[0].body
            #
            addr_proxy_obj = self.env['directory.address.proxy']
            if self.type == 'initial':
                addr_proxy_ids = addr_proxy_obj.search([('user_validated', '=', False), ('send_initial_mail', '=', False), ('sending_address', '<>', False)])
            elif selftype == '1followup':
                addr_proxy_ids = addr_proxy_obj.search([('user_validated', '=', False), ('send_initial_mail', '>', '1980-01-01'), ('send_first_followup', '=', False), ('sending_address', '<>', False)])
            else:
                addr_proxy_ids = []
            sended_emails = []
            sended_ids = []
            errors = []
            if addr_proxy_ids:
                proxies = addr_proxy_ids.read(['id', 'link_id', 'sending_courtesy', 'sending_name', 'sending_courtesy', 'sending_address', 'partner_id'])
                for proxy in proxies:
                    email_content = template.body.replace('[courtesy]', proxy['sending_courtesy'] or '').replace('[name]', proxy['sending_name'] or 'cher Membre').replace('[link_id]', proxy['link_id'])
                    if '[others_data]' in template.body and proxy['partner_id']:
                        other_ids = addr_proxy_obj.search([('partner_id', '=', proxy['partner_id'][0]), ('id', '<>', proxy['id']), ('sending_address', '<>', False), ('user_validated', '=', False)])
                        if other_ids:
                            others = other_ids.read(['complete_name', 'sending_courtesy', 'sending_name', 'sending_address', 'link_id'])
                            others_list = []
                            for other in others:
                                others_list.append(base_item % (other['complete_name'],
                                                                other['sending_name'] and (u'"' + other['sending_courtesy'] + ' ' + other['sending_name'] + '"') or u'l\'adresse du siège',
                                                                other['sending_address'],
                                                                other['link_id'],
                                                                other['link_id']))
                            optional_message = add_message % u'</li><li>'.join(others_list)
                            email_content = email_content.replace('[others_data]', optional_message)
                            # print email_content
                        else:
                            email_content = email_content.replace('[others_data]', '')
                    email_address = proxy['sending_address']
                    # email_address = 'philmer@ccilvn.be' ## TODO delete
                    try:
                        tools.email_send(data['form']['from'], [email_address], data['form']['title'], email_content, subtype='html')
                        # print '---email content---'
                        # print email_content
                    except:
                        errors.append(email_address)
                    else:
                        sended_emails.append(email_address)
                        sended_ids.append(proxy['id'])
                        # recording of the sending after each one, so, if we have a problem, we can determine what is already sent...
                        if data['form']['type'] == 'initial':
                            addr_proxy_obj.write(cr, uid, [proxy['id'], ], {'send_initial_mail':datetime.date.today().strftime('%Y-%m-%d')})
                        elif data['form']['type'] == '1followup':
                            addr_proxy_obj.write(cr, uid, [proxy['id'], ], {'send_first_followup':datetime.date.today().strftime('%Y-%m-%d')})
            results = 'Sended emails : %s\nErrors : %s' % (str(len(sended_emails)), str(len(errors)))
        else:
            results = 'You MUST define template "DirMemberTemplate" and "DirMemberTemplateID"'
            
        ctx = self.env.context.copy()
        ctx.update({'results': results})
        view = self.env.ref('cci_memberdirectory.view_cci_memberdirectory_send_email_msg')
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.memberdirectory.send.email.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_memberdirectory_send_email_msg(models.TransientModel):
    _name = 'cci.memberdirectory.send.email.msg'
    
    results = fields.Text(string='Results', readonly=True, default='')
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_memberdirectory_send_email_msg, self).default_get(fields)
        if self.env.context.get('results'):
            rec['results'] = self.env.context['results']
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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

import random
from openerp import models, fields, api, _
from openerp import tools

class send_website_data(models.TransientModel):
    _name = 'send.website.data'
    
    from_email = fields.Char(string='From', size=64, required=True)
    perso_message = fields.Text(string='Personalized message', help='Not mandatory, appears at top of classical message')
    
    @api.multi
    def send_data(self):
        text = u'''Suite à votre demande, voici votre login et votre mot de passe pour vous connecter sur le site de la CCI Connect : www.cciconnect.be.
    
    Login : %s
    
    Mot de passe : %s
    
    %s
    
    Bienvenue.'''
    
        str_to = 'test@cciconnect.be'
        str_from = ''
        
        partner_id = self.env.context.get('active_id', False)
        
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            str_from = self.from_email or 'nepasrepondre@cciconnect.be'  # # the field is required, this not usefull
            str_to = partner.email or str_to
            # TODO check email address from
            if str_to and str_from:
                if partner.login_name and not partner.login_name in ['jamais', 'autrezone', 'double_email']:
                    text = text % (partner.login_name, partner.password, tools.ustr(self.perso_message or ''))
                    text = tools.ustr(text)
                    res = tools.email_send(str_from, [str_to], 'CCIConnect login et mot de passe', text)
                    if res:
                        res_message = "The login-password has been resend to the email address '%s'" % str_to
                    else:
                        res_message = "Error: Mail not sent, Contact '%s %s' does not have a valid address mail : '%s' or the mail cannot be send" % (partner.name, partner.first_name, str_to)
                else:
                    res_message = "Error: Contact '%s %s' has no valid login_name : '%s'" % (partner.name, partner.first_name, partner.login_name)
                
        view = self.env.ref('cci_base_contact.view_send_website_message_form')
        ctx = self.env.context.copy()
        ctx.update({'message': res_message})
        return {
            'name': _('Result'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.website.message',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class send_website_message(models.TransientModel):
    _name = 'send.website.message'
    
    message = fields.Text('Result', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(send_website_message, self).default_get(fields)
        if self.env.context.get('message'):
            res.update({
                'message': self.env.context['message'],
            })
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class create_website_data(models.TransientModel):
    _name = 'create.website.data'
    
    send_email = fields.Boolean('Send EMail with login-password')
    from_email = fields.Char(string='From', size=64)
    perso_message = fields.Text(string='Personalized Message', help='Not mandatory, appears at top of classical message')
    
    @api.multi
    def create_data(self):
        part_id = self.env.context.get('active_id', False)
        
        if part_id:
            contact = self.env['res.partner'].browse(part_id)
            newlogin = contact.email or False
            if newlogin:
                same = self.env['res.partner'].search([('login_name', '=', newlogin)])
                if not same:
                    random.seed()
                    if contact.name and contact.first_name:
                        newpw = contact.name[0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + contact.first_name[0:2].lower()
                    else:
                        if contact.name and len(contact.name) > 3:
                            newpw = contact.name[0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + contact.name[2:4].lower()
                        else:
                            newpw = contact.name[0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + 'am'
                    if not newpw.isalpha():
                        newpw = newpw.replace('.', '').replace('-', '.')
                    same = True
                    while same:
                        newtoken = hex(random.getrandbits(128))[2:34]
                        same = self.env['res.partner'].search([('token', '=', newtoken)])
                    res = contact.write({'login_name': newlogin, 'password': newpw, 'token': newtoken})
                    if res:
                        res_message = "Login-pw created '%s' / '%s' / '%s'" % (newlogin, newpw, newtoken)
                        if self.send_email and self.from_email:
                                text = u'''Suite à votre demande, voici votre login et votre mot de passe pour vous connecter sur le site de la CCI Connect : www.cciconnect.be.
        
                                Login : %s
                                
                                Mot de passe : %s
                                
                                %s
                                
                                Bienvenue.'''
        
                                str_to = 'test@cciconnect.be'
                                str_from = ''
                                
                                str_from = self.from_email or 'nepasrepondre@cciconnect.be'  # # the field is required, this not usefull
                                str_to = contact.email or str_to
                                # TODO check email address from
                                if str_to and str_from:
                                    text = text % (newlogin, newpw, tools.ustr(self.perso_message or ''))
                                    text = tools.ustr(text)
                                    res = tools.email_send(str_from, [str_to], 'CCIConnect login et mot de passe', text)
                                    if res:
                                        res_message += "\nThe login-password has been send to the email address '%s'" % str_to
                                    else:
                                        res_message += "\nError: Mail not sent, Contact '%s %s' does not have a valid address mail : '%s' or the mail cannot be send" % (contact.name, contact.first_name, str_to)
                    else:
                        res_message = "Error while registering new login-password-token"
                else:
                    res_message = 'An other contact already have the same login : ' + newlogin
            else:
                res_message = "No valid email address for this contact. Creation of login failed"

        view = self.env.ref('cci_base_contact.view_create_website_message_form')
        ctx = self.env.context.copy()
        ctx.update({'message': res_message})
        return {
            'name': _('Result'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.website.message',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class create_website_message(models.TransientModel):
    _name = 'create.website.message'
    
    message = fields.Text('Result', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(create_website_message, self).default_get(fields)
        invoice_ids = rec.get('invoice_ids') and rec['invoice_ids'][0][2] or None
        if self.env.context.get('message'):
            rec['message'] = self.env.context['message']
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
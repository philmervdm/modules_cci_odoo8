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
import time
import datetime
from openerp import tools
import base64
from xlwt import *

class send_new_login(models.TransientModel):

    _name = 'send.new.login'
    
    template = fields.Many2one('email.template', string='Template', required=True)
    forced = fields.Boolean(string=u'Même aux login/pw existants ?')
    email_from = fields.Char(string='Email From', size=120, required=True)
    
    @api.multi
    def send_mails(self):
        obj_contact = self.env['res.partner']
        #msg = 'Resultats : ' + ','.join(obj_contact.get_complex_id_from_id(data['ids']))
        (sended,no_email_address,existing) = obj_contact.send_new_login_form(self.env.context.get('active_ids',[]),self.template,self.forced,self.email_from)
        # give the result tos the user
        msg = u"""Envois effectués :
                  \nEmails envoyés aux adresses suivantes : %s
                  \n\nPas d'email envoyé aux ID de contact suivants parce que pas d'adresse email : %s
                  \n\nPas d'email envoyés aux ID de contact suivant parce que login/pw existant : %s""" % (sended and ','.join(sended) or u'aucun',
                                                                                                           no_email_address and ','.join([str(x) for x in no_email_address]) or u'aucun',
                                                                                                           existing and ','.join([str(x) for x in existing]) or u'aucun' )
        
        
        res={}
        res['msg'] = msg
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.new.login.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': res,
        }
        
class send_new_login_msg(models.TransientModel):

    _name = 'send.new.login.msg'
    
    msg = fields.Text(string = 'File created',readonly = True)

    @api.model
    def default_get(self, fields):
        res = super(send_new_login_msg, self).default_get(fields)
        res.update({'msg': self.env.context.get('msg','')})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


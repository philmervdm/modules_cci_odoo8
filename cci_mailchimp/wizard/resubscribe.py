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
# This wizard unsubscribe the user from the list and force the deleting of the user to permit the re-subsribe of this user

import time
import datetime
#import mailchimp
from openerp import models, fields, api, _

class cci_mailchimp_resubscribe(models.TransientModel):
    _name = 'cci.mailchimp.resubscribe'
    
    confirm = fields.Boolean(string='Confirmation', help='You must confirm you\'re trying to SPAM this user')
    
    @api.multi
    def resubscribe(self):
        obj_bounce = self.env['mail_bounce']
        bounce_email = obj_bounce.read(data['id'], ['name'])['name']
        if bounce_email:
            # We get the API key
            parameter_obj = self.env['ir.config_parameter']
            param_values = parameter_obj.get_param(['MailChimpAPIKey', 'MailChimpRDPListID'])
            treated = True
            if param_values.has_key('MailChimpAPIKey') and param_values.has_key('MailChimpRDPListID'):
                MailChimpAPIKey = param_values['MailChimpAPIKey']
                mailchimp_list_id = param_values['MailChimpRDPListID']
                mailchimp_server = mailchimp.Mailchimp(MailChimpAPIKey, False)
                mailchimp_lists = mailchimp.Lists(mailchimp_server)
                try:
                    result = mailchimp_lists.unsubscribe(mailchimp_list_id, {'email':bounce_email}, True)
                except mailchimp.EmailNotExistsError:
                    treated = True
                except:
                    treated = False
                    
            if treated:
                bounce = obj_bounce.browse(self.env.context['active_id'])
                bounce.write({'active':False})
                obj_contact = self.env['res.partner']
                contact = obj_contact.search([('email', '=', bounce_email), ('rdp_subscribe', '=', 'unsubscribed')])
                if contact:
                    contact.write({'rdp_subscribe': 'default'})
                obj_job = self.env['res.partner']
                jobs = obj_job.search([('email', '=', bounce_email)])
                if jobs:
                    for job in jobs:
                        if job.contact_id and job.contact_id.rdp_subscribe == 'unsubscribed':
                            job.contact_id.write({'rdp_subscribe': 'default'})
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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
#         1.1 Philmer added some extra fields and re-ordered them in excel file
#         1.2 Philmer added name of patrner_invoiced for management of 'les mais de mes amis'
import time
import datetime
# import re
from openerp import tools
import base64
from xlwt import *
from openerp import models, fields, api, _

class event_extract_registrations(models.Model):
    _name = 'event.extract.registrations'
    
    choice = fields.Selection(string='Selection', selection=[('all', 'Toutes les inscriptions'), ('selected', 'Seulement les actives')], required= True, default='all')
    
    @api.multi
    def get_file(self):
        obj_registration = self.env['event.registration']
        if self.choice == 'all':
            reg_ids = obj_registration.search([('event_id', 'in', self.env.context['active_ids'])])
        else:
            reg_ids = obj_registration.search([('event_id', 'in', self.env.context['active_ids']), ('state', 'in', ['open', 'done'])])
        
        if reg_ids:
            registrations = reg_ids
        else:
            registrations = []

        wb1 = Workbook()
        ws1 = wb1.add_sheet('Inscriptions')
        ws1.write(0, 0, 'partner_name')
#         ws1.write(0, 1, 'contact_name')
#         ws1.write(0, 2, 'contact_first_name')
        ws1.write(0, 1, 'street')
        ws1.write(0, 2, 'street2')
        ws1.write(0, 3, 'zip_code')
        ws1.write(0, 4, 'city')
        ws1.write(0, 5, 'phone_address')
        ws1.write(0, 6, 'fax_address')
#         ws1.write(0, 7, 'email')
#         ws1.write(0, 10, 'badge_partner')
#         ws1.write(0, 11, 'badge_name')
        ws1.write(0, 7, 'registration_state')
#         ws1.write(0, 8, 'courtesy')
#         ws1.write(0, 14, 'badge_title')
        ws1.write(0, 8, 'event_name')
#         ws1.write(0, 10, 'unit_price')
        ws1.write(0, 9, 'event_id')
        ws1.write(0, 10, 'registration_id')
        ws1.write(0, 11, 'partner_id')
#         ws1.write(0, 20, 'partner_invoice_id')
#         ws1.write(0, 21, 'partner_invoice_name')
#         ws1.write(0, 22, 'contact_id')
        ws1.write(0, 12, 'partner_membership_state')
        ws1.write(0, 13, 'nb_register')
        ws1.write(0, 14, 'ask_attest')
        ws1.write(0, 15, 'cavalier')
        ws1.write(0, 16, 'comments')
#         ws1.write(0, 17, 'group_name')
#         ws1.write(0, 17, 'invoice_number')
#         ws1.write(0, 22, 'job_id')
        ws1.write(0, 17, 'address_id')
        line = 1
        for reg in registrations:
            # search for the address of the contact
            job_id = address_id = 0
            street = street2 = zip_code = city = addr_phone = addr_fax = job_email = ''
            if reg.contact_id:
                for job in reg.contact_id.other_contact_ids:
                    if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == reg.partner_id.id:
                        street = job.address_id.street
                        street2 = job.address_id.street2
                        if job.address_id.zip_id:
                            zip_code = job.address_id.zip_id.name
                            city = job.address_id.zip_id.city
                        addr_phone = job.address_id.phone
                        addr_fax = job.address_id.fax
                        job_email = job.email
                        job_id = job.id
                        address_id = job.address_id.id
            if job_id == 0 and reg.partner_id:
                # we found no address between partner_id and contact_id, then we take the default address of the partner
                for address in reg.partner_id.child_ids:
                    if address.type == 'default':
                        street = address.street
                        street2 = address.street2
                        if address.zip_id:
                            zip_code = address.zip_id.name
                            city = address.zip_id.city
                        addr_phone = address.phone
                        addr_fax = address.fax
                        address_id = address.id
            ws1.write(line, 0, reg.partner_id.name or '')
#             ws1.write(line, 1, reg.contact_id.name or '')
#             ws1.write(line, 2, reg.contact_id.first_name or '')
            # ws1.write(0,3,'street')
            # ws1.write(0,4,'street2')
            # ws1.write(0,5,'zip_code')
            # ws1.write(0,6,'city')
            # ws1.write(0,7,'phone_address')
            # ws1.write(0,8,'fax_address')
            # ws1.write(0,9,'email')
            ws1.write(line, 1, street or '')
            ws1.write(line, 2, street2 or '')
            ws1.write(line, 3, zip_code or '')
            ws1.write(line, 4, city or '')
            ws1.write(line, 5, addr_phone or '')
            ws1.write(line, 6, addr_fax or '')
#             ws1.write(line, 7, reg.email_from or job_email or '')
#             ws1.write(line, 10, reg.badge_partner or '')
#             ws1.write(line, 11, reg.badge_name or '')
            ws1.write(line, 7, reg.state or '')
#             ws1.write(line, 13, reg.contact_id.title or '')
#             ws1.write(line, 14, reg.badge_title or '')
            ws1.write(line, 8, reg.event_id.name)
#             ws1.write(line, 9, reg.unit_price or 0.0)
            ws1.write(line, 9, reg.event_id.id)
            ws1.write(line, 10, reg.id)
            ws1.write(line, 11, reg.partner_id.id)
#             ws1.write(line, 20, reg.partner_invoice_id.id)
#             ws1.write(line, 21, reg.partner_invoice_id.name)
#             ws1.write(line, 22, reg.contact_id.id)
            ws1.write(line, 12, reg.partner_id.membership_state or '')
            ws1.write(line, 13, reg.nb_register or '')
            ws1.write(line, 14, reg.ask_attest and 'Oui' or 'Non')
            ws1.write(line, 15, reg.cavalier and 'Oui' or 'Non')
            ws1.write(line, 16, reg.comments or '')
#             ws1.write(line, 17, reg.group_id and reg.group_id.name or '')
#             ws1.write(line, 17, reg.invoice_id and reg_invoice_id.number or '')
#             ws1.write(line, 30, job_id or 0)
            ws1.write(line, 17, address_id or 0)
            line += 1
        wb1.save('registrations.xls')
        result_file = open('registrations.xls', 'rb').read()

        # give the result tos the user
        msg = 'Save the File with '".xls"' extension.'
        inscriptions = base64.encodestring(result_file)
        
        ctx = self.env.context.copy()
        
        ctx.update({'msg': msg, 'inscriptions': inscriptions, 'name': 'registrations.xls'})
        
        resource = self.env.ref('cci_event.event_extract_registrations_msg_view_form')
        return {
            'name': 'Registrations',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.extract.registrations.msg',
            'views': [(resource.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

class event_extract_registrations_msg(models.TransientModel):
    _name = 'event.extract.registrations.msg'
    
    name = fields.Char('Name')
    msg = fields.Text('File created', readonly=True)
    inscriptions = fields.Binary(string='Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(event_extract_registrations_msg, self).default_get(fields)
        if self.env.context.has_key('name'):
            res.update({'name': self.env.context['name']})
            
        if self.env.context.has_key('msg'):
            res.update({'msg': self.env.context['msg']})
        
        if self.env.context.has_key('inscriptions'):
            res.update({'inscriptions': self.env.context['inscriptions']})
        return res 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

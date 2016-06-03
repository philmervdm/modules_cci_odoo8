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
# Version 1.0 Philmer redefined from cci_event/wizard/extract_registrations.py with the addition of the extraction of the activity sector
#         1.1 Philmer added vat from invoiced partner in output file
#         1.2 Philmer added birthdate for Vincent Mausen
#         1.3 Philmer added Salesmna for Benjamin Lecron

from xlwt import *
import time
import datetime
import base64
from openerp import tools
from openerp import models, fields, api, _

class extract_registrations_with_activity(models.TransientModel):
    _name = 'extract.registrations.with.activity'
    
    choice = fields.Selection(selection=[('all','Toutes les inscriptions'),('selected','Seulement les actives')], required=True, string='Selection', default='all')
    category_id = fields.Many2one('res.partner.category', string='Activity Sectors Root', required=True)
    
    @api.multi
    def get_file(self):
        obj_registration = self.env['event.registration']

        # extract all ids of activity sector categories and remove '[303]' from name
        obj_categ = self.env['res.partner.category']
        old_len = 0
        categ_ids = [self.category_id.id]
        while len(categ_ids) > old_len:
            new_ids = categ_ids[old_len:]  # ids of categories added last time
            old_len = len(categ_ids)  # the new frontier ...
            new_ids = obj_categ.browse(new_ids)
            new_categs = new_ids.read(['child_ids'])
            for categ in new_categs:
                if categ['child_ids']:
                    categ_ids.extend(categ['child_ids'])
        
        categ_ids = obj_categ.browse(categ_ids)
        categs = categ_ids.with_context({'lang':'fr_FR'}).read(['name'])
        dCategs = {}
        for categ in categs:
            formated_name = categ['name']
            posA = formated_name.rfind('[')
            posB = formated_name.rfind(']')
            if posA > 0 and posB > 0 and posA < posB:
                formated_name = formated_name[0:posA - 1]
            dCategs[categ['id']] = formated_name

        # search the registrations linked to the selected events
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
        ws1.write(0, 1, 'contact_name')
        ws1.write(0, 2, 'contact_first_name')
        ws1.write(0, 3, 'street')
        ws1.write(0, 4, 'street2')
        ws1.write(0, 5, 'zip_code')
        ws1.write(0, 6, 'city')
        ws1.write(0, 7, 'phone_address')
        ws1.write(0, 8, 'fax_address')
        ws1.write(0, 9, 'email')
        ws1.write(0, 10, 'badge_partner')
        ws1.write(0, 11, 'badge_name')
        ws1.write(0, 12, 'registration_state')
        ws1.write(0, 13, 'courtesy')
        ws1.write(0, 14, 'badge_title')
        ws1.write(0, 15, 'event_name')
        ws1.write(0, 16, 'unit_price')
        ws1.write(0, 17, 'event_id')
        ws1.write(0, 18, 'registration_id')
        ws1.write(0, 19, 'partner_id')
        ws1.write(0, 20, 'partner_invoice_id')
        ws1.write(0, 21, 'partner_invoice_name')
        ws1.write(0, 22, 'activity_sector')
        ws1.write(0, 23, 'contact_id')
        ws1.write(0, 24, 'partner_membership_state')
        ws1.write(0, 25, 'nb_register')
        ws1.write(0, 26, 'ask_attest')
        ws1.write(0, 27, 'cavalier')
        ws1.write(0, 28, 'comments')
        ws1.write(0, 29, 'group_name')
        ws1.write(0, 30, 'invoice_number')
        ws1.write(0, 31, 'job_id')
        ws1.write(0, 32, 'address_id')
        ws1.write(0, 33, 'name_directory')
        ws1.write(0, 34, 'Invoices VAT')
        ws1.write(0, 35, 'Birth Date')
        ws1.write(0, 36, 'Salesman')
        line = 1
        
        for reg in registrations:
            # search for the address of the contact
            job_id = address_id = 0
            street = street2 = zip_code = city = addr_phone = addr_fax = job_email = ''
#             if reg.contact_id:
#                 for job in reg.contact_id.job_ids:
#                     if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == reg.partner_id.id:
#                         street = job.address_id.street
#                         street2 = job.address_id.street2
#                         if job.address_id.zip_id:
#                             zip_code = job.address_id.zip_id.name
#                             city = job.address_id.zip_id.city
#                         addr_phone = job.address_id.phone
#                         addr_fax = job.address_id.fax
#                         job_email = job.email
#                         job_id = job.id
#                         address_id = job.address_id.id
                        
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
            ws1.write(line, 3, street or '')
            ws1.write(line, 4, street2 or '')
            ws1.write(line, 5, zip_code or '')
            ws1.write(line, 6, city or '')
            ws1.write(line, 7, addr_phone or '')
            ws1.write(line, 8, addr_fax or '')
#             ws1.write(line, 9, reg.email_from or job_email or '')
#             ws1.write(line, 10, reg.badge_partner or '')
#             ws1.write(line, 11, reg.badge_name or '')
            ws1.write(line, 12, reg.state or '')
#             ws1.write(line, 13, reg.contact_id.title or '')
#             ws1.write(line, 14, reg.badge_title or '')
            ws1.write(line, 15, reg.event_id.name)
#             ws1.write(line, 16, reg.unit_price or 0.0)
            ws1.write(line, 17, reg.event_id.id)
            ws1.write(line, 18, reg.id)
            ws1.write(line, 19, reg.partner_id.id)
#             ws1.write(line, 20, reg.partner_invoice_id.id)
#             ws1.write(line, 21, reg.partner_invoice_id.name)
            if reg.partner_id and reg.partner_id.category_id:
                for categ in reg.partner_id.category_id:  # # category_id is, not like his name define, an array of category ids
                    if categ.id in categ_ids.ids:
                        ws1.write(line, 22, dCategs[categ.id])
                        break
#             ws1.write(line, 23, reg.contact_id.id)
            ws1.write(line, 24, reg.partner_id.membership_state or '')
            ws1.write(line, 25, reg.nb_register or '')
#             ws1.write(line, 26, reg.ask_attest and 'Oui' or 'Non')
#             ws1.write(line, 27, reg.cavalier and 'Oui' or 'Non')
            ws1.write(line, 28, reg.comments or '')
#             ws1.write(line, 29, reg.group_id and reg.group_id.name or '')
#             ws1.write(line, 30, reg.invoice_id and reg_invoice_id.number or '')
#             ws1.write(line, 31, job_id or 0)
            ws1.write(line, 32, address_id or 0)
            ws1.write(line, 33, reg.partner_id.dir_name or reg.partner_id.name or '')
#             ws1.write(line, 34, reg.partner_invoice_id.vat and reg.partner_invoice_id.vat or '')
#             ws1.write(line, 35, reg.contact_id.birthdate or '')
#             ws1.write(line, 36, reg.partner_invoice_id.user_id and reg.partner_invoice_id.user_id.name or '')
            line += 1
        wb1.save('registrations.xls')
        result_file = open('registrations.xls', 'rb').read()
        
        ctx = self.env.context.copy()
        # give the result tos the user
        msg = 'Save the File with '".xls"' extension.'
        inscriptions_xls = base64.encodestring(result_file)
        ctx.update({'msg': msg, 'inscriptions_xls': inscriptions_xls, 'name': 'inscriptions.xls'})
        
        
        resource = self.env.ref('cci_event_extend.cci_extract_registrations_with_activity_msg_view')
        return {
            'name': 'Notification',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'extract.registrations.with.activity.msg',
            'views': [(resource.id, 'form')],
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class extract_registrations_with_activity_msg(models.TransientModel):
    _name = 'extract.registrations.with.activity.msg'
    
    name = fields.Char(string='Name')
    msg = fields.Text('File created', readonly=True)
    inscriptions_xls = fields.Binary('Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(extract_registrations_with_activity_msg, self).default_get(fields)
        if 'name' in self.env.context:
            res.update({'name': self.env.context['name']})
        if 'msg' in self.env.context:
            res.update({'msg': self.env.context['msg']})
        if 'inscriptions_xls' in self.env.context:
            res.update({'inscriptions_xls': self.env.context['inscriptions_xls']})
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

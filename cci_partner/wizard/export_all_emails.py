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

import StringIO
import base64
import time
from openerp import models, fields, api, _

class export_all_emails_finish (models.TransientModel):
    _name = 'export.all.emails'
    
    address = fields.Boolean(string='Emails from addresses')
#     job = fields.Boolean(string='Emails from Jobs')
#     contact = fields.Boolean(string='Emails from Contacts')
    tag_ids = fields.Many2many('crm_profiling.answer', 'crm_profiling_answer_export_all_emails_rel', 'export_email_id', 'profiling_id', string='Additionnal tags',)
    format = fields.Selection([('excel', 'Excel File'), ('csv', 'CSV File')], string='Format of the file', default='csv')
    
    @api.multi
    def make_file(self):
        emails_list = []
        emails_source = []
#         if self.job:
#             self.env.cr.execute("select job.id from res_partner_job as job, res_partner_address as addr, res_partner as partner where job.address_id = addr.id and addr.partner_id = partner.id and partner.membership_state in ('free','invoiced','paid') and job.email is not null and char_length(job.email)>4")
#             res = cr.fetchall()
#             job_ids = [ x[0] for x in res ]
#             jobs = self.env['res.partner.job'].read(cr, uid, job_ids, ['id', 'email'])
#             for job in jobs:
#                 if job['email'] not in emails_list:
#                     emails_list.append(job['email'])
#                     emails_source.append('Job(%s)' % str(job['id']))
        if self.address:
            self.env.cr.execute("select addr.id from res_partner as addr, res_partner as partner where addr.parent_id = partner.id and partner.membership_state in ('free','invoiced','paid') and addr.email is not null and char_length(addr.email)>4")
            res = self.env.cr.fetchall()
            addr_ids = [ x[0] for x in res ]
            addr = self.env['res.partner'].browse(addr_ids)
            addresses = addr.read(['id', 'email'])
            for addr in addresses:
                if addr['email'] not in emails_list:
                    emails_list.append(addr['email'])
                    emails_source.append('Address(%s)' % str(addr['id']))
#         if self.contact:
#             contact_obj = self.env['res.partner.contact']
#             contact_ids = contact_obj.search([('email', '<>', False)])
#             contacts = contact_obj.browse(cr, uid, contact_ids)
#             for cont in contacts:
#                 if cont.email not in emails_list:
#                     # check if linked to a member
#                     for job in cont.job_ids:
#                         if job.address_id and job.address_id.partner_id and job.address_id.partner_id.membership_state in ['paid', 'invoiced', 'free']:
#                             emails_list.append(cont.email)
#                             emails_source.append('Contact(%s)' % str(cont.id))
#                             break
        # extract emails from selected tags
        answer_obj = self.env['crm_profiling.answer']
        for answer in self.tag_ids:
            # determine the type of linked table
#             if answer.question_id.target == 'res.partner':
#                 # nothing to do because a partner has no address
#                 # perhasp, select all email from addresses linked to theses partners...
#                 pass
#             if answer.question_id.target == 'res.partner':
            self.env.cr.execute("select addr.id from res_partner as addr, partner_question_rel as link where addr.id = link.partner and link.answer = %s and addr.email is not null and char_length(addr.email)>4" % str(answer.id))
            res = self.env.cr.fetchall()
            addr_ids = [ x[0] for x in res ]
            addrs = self.env['res.partner'].browse(addr_ids)
            addresses = addrs.read(['id', 'email'])
            for addr in addresses:
                if addr['email'] not in emails_list:
                    emails_list.append(addr['email'])
                    emails_source.append('Address(%s)-Tag(%s)' % (str(addr['id']), answer.question_id.name + '=' + answer.name))
#             elif answer.question_id.target == 'res.partner.job':
#                 cr.execute("select job.id from res_partner_job as job, jobs_question_rel as link where job.id = link.job and link.answer = %s and job.email is not null and char_length(job.email)>4" % str(answer.id))
#                 res = cr.fetchall()
#                 job_ids = [ x[0] for x in res ]
#                 jobs = self.env['res.partner.job'].read(cr, uid, job_ids, ['id', 'email'])
#                 for job in jobs:
#                     if job['email'] not in emails_list:
#                         emails_list.append(job['email'])
#                         emails_source.append('Job(%s)-Tag(%s)' % (str(job['id']), answer.question_id.name + '=' + answer.name))
#             elif answer.question_id.target == 'res.partner.contact':
#                 cr.execute("select contact.id from res_partner_contact as contact, contact_question_rel as link where contact.id = link.contact and link.answer = %s and contact.email is not null and char_length(contact.email)>4" % str(answer.id))
#                 res = cr.fetchall()
#                 cont_ids = [ x[0] for x in res ]
#                 contacts = self.env['res.partner.contact'].read(cr, uid, cont_ids, ['id', 'email'])
#                 for contact in contacts:
#                     if contact['email'] not in emails_list:
#                         emails_list.append(contact['email'])
#                         emails_source.append('Contact(%s)-Tag(%s)' % (str(contact['id']), answer.question_id.name + '=' + answer.name))
        # export result to the desired format
        file = StringIO.StringIO()
        if self.format == 'excel':
            import xlwt as xl
            wb = xl.Workbook()
            ws = wb.add_sheet("emails")
            ws.write(0, 0, 'email')
            ws.write(0, 1, 'source')
            line = 1
            for index in xrange(0, len(emails_list)):
                ws.write(line, 0, emails_list[index])
                ws.write(line, 1, emails_source[index])
                line += 1
            wb.save(file)
            extension = 'xls'
        else:  # CSV
            import csv
            hfCSV = csv.writer(file)  # standard format not excel one because there is a direct excel export...
            hfCSV.writerow(['email', 'source'])
            for index in xrange(0, len(emails_list)):
                hfCSV.writerow([emails_list[index].encode('cp1252'), emails_source[index]])
            extension = 'csv'
        out = base64.encodestring(file.getvalue())
        
        ctx = dict(self.env.context or {})
        ctx.update({'data': out , 'file_name': 'all_emails_members_%s.%s' % (time.strftime('%Y-%m-%d'), extension)})
        view = self.env.ref('cci_partner.export_all_emails_finish_form')
        return {
            'name': _('Export all Emails of Members'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'export.all.emails.finish',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }
    
class export_all_emails_finish(models.TransientModel):
    _name = 'export.all.emails.finish'
    
    data = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    
    @api.model
    def default_get(self, fields):
        res = super(export_all_emails_finish, self).default_get(fields)
        data = False
        filename = False
        if self.env.context.has_key('data'):
            data = self.env.context['data']
        if self.env.context.has_key('file_name'):
            filename = self.env.context['file_name']
            
        res.update({'data': data, 'file_name': filename})
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

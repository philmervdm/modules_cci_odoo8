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
from openerp import models, fields, api
import time
import datetime
from openerp import tools
import base64
from xlwt import *


class extract_premium_data(models.TransientModel):
    _name = 'extract.premium.data'

    choice = fields.Selection([('contact','Seulement les données \'Personnes de contact\''),('all','Tout')], string='Selection', required = True, default = 'all')

    @api.multi
    def getfile(self):
        obj_contact = self.env['res.partner']
        contacts = obj_contact.search([('is_premium','=','OUI')])
#         if contact_ids:
#             contacts = obj_contact.browse(cr,uid,contact_ids)
#         else:
#             contacts = []

        wb1 = Workbook()
        ws1 = wb1.add_sheet('Premium')
        ws1.write(0,0,'contact_suite')
        ws1.write(0,17,'contact_id')
        ws1.write(0,16,'job_id')
        ws1.write(0,15,'address_id')
        ws1.write(0,14,'partner_id')
        ws1.write(0,1,'sequence_contact')
        ws1.write(0,6,'last_name')
        ws1.write(0,7,'first_name')
        ws1.write(0,5,'courtesy')
        ws1.write(0,21,'perso_email')
        ws1.write(0,38,'mobile')
        ws1.write(0,39,'begin_premium')
        ws1.write(0,40,'end_premium')
        ws1.write(0,34,'function_code_label')
        ws1.write(0,8,'function_label')
        ws1.write(0,20,'prof_email')
        ws1.write(0,9,'street')
        ws1.write(0,10,'street2')
        ws1.write(0,11,'zip_code')
        ws1.write(0,12,'city')
        ws1.write(0,35,'addr_name')
        ws1.write(0,24,'addr_email')
        ws1.write(0,22,'phone')
        ws1.write(0,23,'fax')
        ws1.write(0,36,'addr_employee_nbr')
        ws1.write(0,4,'company_name')
        ws1.write(0,30,'full_company_name')
        ws1.write(0,28,'company_employee_nbr')
        ws1.write(0,37,'company_employee_nbr_total')
        ws1.write(0,13,'zip_country')
        ws1.write(0,25,'vat')
        ws1.write(0,26,'salesman')
        ws1.write(0,31,'address_activ1')
        ws1.write(0,32,'address_activ1')
        ws1.write(0,33,'address_activ1')
        ws1.write(0,2,'membership')
        ws1.write(0,3,'company_title')
        ws1.write(0,18,'job_phone')
        ws1.write(0,19,'job_fax')
        ws1.write(0,27,'partner_state')
        ws1.write(0,29,'partner_website')
        line = 1
        for contact in contacts:
            contact_suite = 1
            # step 1 : here because a contact can have no jobs
            ws1.write(line,0,contact_suite)
            ws1.write(line,17,contact.id)
            ws1.write(line,6,contact.name)
            ws1.write(line,7,contact.first_name or '')
            ws1.write(line,5,contact.title and contact.title.name or '')
            ws1.write(line,21,contact.email or '')
            ws1.write(line,38,contact.mobile or '')
            ws1.write(line,39,contact.premium_begin or '')
            ws1.write(line,40,contact.premium_end or '')
            # sort the jobs of this contact following sequence_contact
            if contact.other_contact_ids:
                jobs = []
                for job in contact.other_contact_ids:
                    jobs.append({'job':job})#,'sequence_contact':job.sequence_contact or 99})
#                 jobs = sorted(jobs, key=lambda k: k['sequence_contact'])
                 
                for job_sorted in jobs:
                    current_job = job_sorted['job']
                    if contact_suite > 1: ## re-indicate the data from the contact, but must stay on step 1 because a contact can have no jobs
                        ws1.write(line,0,contact_suite)
                        ws1.write(line,17,contact.id)
                        ws1.write(line,6,contact.name)
                        ws1.write(line,7,contact.first_name or '')
                        ws1.write(line,5,contact.title and contact.title.name or '')
                        ws1.write(line,21,contact.email or '')
                        ws1.write(line,38,contact.mobile or '')
                        ws1.write(line,39,contact.premium_begin or '')
                        ws1.write(line,40,contact.premium_end or '')
                    ws1.write(line,16,current_job.id)
#                     ws1.write(line,1,current_job.sequence_contact or 99)
                    ws1.write(line,34,current_job.function_code_label or '')
                    ws1.write(line,8,current_job.function_label or '')
                    ws1.write(line,20,current_job.email or '')
                    ws1.write(line,18,current_job.phone or '')
                    ws1.write(line,19,current_job.fax or '')
                    if current_job.address_id:
                        ws1.write(line,15,current_job.address_id.id)
                        ws1.write(line,9,current_job.address_id.street or '')
                        ws1.write(line,10,current_job.address_id.street2 or '')
                        ws1.write(line,11,current_job.address_id.zip_id and current_job.address_id.zip_id.name or '')
                        ws1.write(line,12,current_job.address_id.zip_id and current_job.address_id.zip_id.city or '')
                        ws1.write(line,35,current_job.address_id.name or '')
                        ws1.write(line,24,current_job.address_id.email or '')
                        ws1.write(line,22,current_job.address_id.phone or '')
                        ws1.write(line,23,current_job.address_id.fax or '')
                        ws1.write(line,36,current_job.address_id.local_employee or -1)
                        ws1.write(line,13,current_job.address_id.country_id and current_job.address_id.country_id.name or '')
                        ws1.write(line,31,current_job.address_id.sector1 and current_job.address_id.sector1.name or '')
                        ws1.write(line,32,current_job.address_id.sector2 and current_job.address_id.sector2.name or '')
                        ws1.write(line,33,current_job.address_id.sector3 and current_job.address_id.sector3.name or '')
                        if current_job.address_id.parent_id:
                            ws1.write(line,14,current_job.address_id.parent_id.id)
                            ws1.write(line,4,current_job.address_id.parent_id.name)
                            if current_job.address_id.name:
                                if current_job.address_id.name[0:2] == '- ':
                                    ws1.write(line,30,current_job.address_id.name + ' ' + current_job.address_id.parent_id.name)
                                elif current_job.address_id.name[0:3] == ' - ':
                                    ws1.write(line,30,current_job.address_id.name + current_job.address_id.parent_id.name)
                                else:
                                    ws1.write(line,30,current_job.address_id.name)
                            else:
                                ws1.write(line,30,current_job.address_id.parent_id.name)
                            ws1.write(line,28,current_job.address_id.parent_id.employee_nbr or -1)
                            ws1.write(line,37,current_job.address_id.parent_id.employee_nbr_total or -1)
                            ws1.write(line,25,current_job.address_id.parent_id.vat or '')
                            ws1.write(line,26,current_job.address_id.parent_id.user_id and current_job.address_id.parent_id.user_id.name or '')
                            ws1.write(line,2,current_job.address_id.parent_id.membership_state)
                            ws1.write(line,3,current_job.address_id.parent_id.title and contact.title.name or '')
                            ws1.write(line,27,current_job.address_id.parent_id.state_id and current_job.address_id.parent_id.state_id.name or '')
                            ws1.write(line,29,current_job.address_id.parent_id.website or '')
                    line += 1
                    if self.choice == 'contact':
                        break
                    else:
                        contact_suite += 1
            else:
                line += 1
        wb1.save('premium.xls')
        result_file = open('premium.xls','rb').read()
        res = {'msg':'Save the File with '".xls"' extension.','premium':base64.encodestring(result_file)}
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'extract.msg.data',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': res,
        }
    
class extract_mag_data(models.TransientModel):
    _name = 'extract.msg.data'

    msg = fields.Text(string='File created', readonly=True)
    premium = fields.Binary(string='Prepared file', readonly=True)
    name = fields.Char('File Name')
    @api.model
    def default_get(self, fields):
        res = super(extract_mag_data, self).default_get(fields)
        res.update({'name':'premium.xls','msg': self.env.context.get('msg',''), 'premium': self.env.context.get('premium',False)})
        return res

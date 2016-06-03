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

import time
import datetime
from openerp import tools
from openerp import models, fields, api, _
import base64
from xlwt import *

class cci_memberdirectory_extract_paper(models.TransientModel):
    _name = 'cci.memberdirectory.extract.paper'
    
    @api.multi
    def get_file(self):
        obj_proxy = self.env['directory.address.proxy']

        # extract all ids of activity sector categories and remove '[303]' from name
        obj_categ = self.env['res.partner.activsector']
        categ_ids = obj_categ.search([])
        categs = categ_ids.read(['code', 'name'])
        dCategs = {}
        for categ in categs:
            dCategs[categ['code']] = categ['name']

        proxies = obj_proxy.browse(self.env.context['active_ids'])
        max_jobs = 5
        for proxy in proxies:
            max_jobs = max(max_jobs, len(proxy.job_ids))
        wb1 = Workbook()
        ws1 = wb1.add_sheet('Addresses')
        ws1.write(0, 0, 'partner_id')
        ws1.write(0, 1, 'address_id')
        ws1.write(0, 2, 'link_id')
        ws1.write(0, 3, 'complete_name')
        ws1.write(0, 4, 'street')
        ws1.write(0, 5, 'zip_code')
        ws1.write(0, 6, 'city')
        ws1.write(0, 7, 'phone_address')
        ws1.write(0, 8, 'fax_address')
        ws1.write(0, 9, 'email')
        ws1.write(0, 10, 'web')
        ws1.write(0, 11, 'vat_num')
        ws1.write(0, 12, 'employee')
        ws1.write(0, 13, 'desc_activ')
        ws1.write(0, 14, 'sector1code')
        ws1.write(0, 15, 'sector2code')
        ws1.write(0, 16, 'sector3code')
        ws1.write(0, 17, 'sector1lib')
        ws1.write(0, 18, 'sector2lib')
        ws1.write(0, 19, 'sector3lib')
        for count_job in range(1, max_jobs + 1):
            ws1.write(0, 13 + (7 * count_job), 'courtesy' + str(count_job))
            ws1.write(0, 14 + (7 * count_job), 'firstname' + str(count_job))
            ws1.write(0, 15 + (7 * count_job), 'lastname' + str(count_job))
            ws1.write(0, 16 + (7 * count_job), 'title' + str(count_job))
            ws1.write(0, 17 + (7 * count_job), 'email' + str(count_job))
            ws1.write(0, 18 + (7 * count_job), 'mobile' + str(count_job))
            ws1.write(0, 19 + (7 * count_job), 'mob_conf' + str(count_job))
        max_jobs = 0
        line = 1
        for proxy in proxies:
            ws1.write(line, 0, proxy.partner_id.id)
            ws1.write(line, 1, proxy.address_id.id)
            ws1.write(line, 2, proxy.link_id)
            ws1.write(line, 3, proxy.complete_name or '')
            complete_street = ''
            if proxy.street:
                complete_street = proxy.street
                if proxy.street_number:
                    complete_street += ', ' + proxy.street_number
                if proxy.street_box:
                    complete_street += ' BTE ' + proxy.street_box
            ws1.write(line, 4, complete_street)
            ws1.write(line, 5, proxy.zip_code or '')
            ws1.write(line, 6, proxy.city or '')
            ws1.write(line, 7, proxy.phone or '')
            ws1.write(line, 8, proxy.fax or '')
            ws1.write(line, 9, proxy.email or '')
            ws1.write(line, 10, proxy.web or '')
            ws1.write(line, 11, proxy.vat_num or '')
            ws1.write(line, 12, proxy.employee or'')
            ws1.write(line, 13, proxy.desc_activ or '')
            ws1.write(line, 14, proxy.sector1 or '')
            ws1.write(line, 15, proxy.sector2 or '')
            ws1.write(line, 16, proxy.sector3 or '')
            ws1.write(line, 17, (proxy.sector1 and dCategs.has_key(proxy.sector1)) and dCategs[proxy.sector1] or '')
            ws1.write(line, 18, (proxy.sector2 and dCategs.has_key(proxy.sector2)) and dCategs[proxy.sector2] or '')
            ws1.write(line, 19, (proxy.sector3 and dCategs.has_key(proxy.sector3)) and dCategs[proxy.sector3] or '')
            contacts = []
            max_jobs = max(max_jobs, len(proxy.job_ids))
            for job in proxy.job_ids:
                if job.last_name:
                    contacts.append({
                         'sequence':job.sequence,
                         'first_name':job.first_name,
                         'last_name':job.last_name or '',
                         'courtesy':job.final_courtesy or '',
                         'title':job.title or '',
                         'email':job.email or '',
                         'mobile':job.mobile or '',
                         'mobile_conf':job.mobile_confidential and 'OUI' or 'Non',
                    })
            sorted(contacts, key=lambda x: x['sequence'])
            index = 1
            for contact in contacts:
                ws1.write(line, (index * 7) + 13, contact['courtesy'])
                ws1.write(line, (index * 7) + 14, contact['first_name'])
                ws1.write(line, (index * 7) + 15, contact['last_name'])
                ws1.write(line, (index * 7) + 16, contact['title'])
                ws1.write(line, (index * 7) + 17, contact['email'])
                ws1.write(line, (index * 7) + 18, contact['mobile'])
                ws1.write(line, (index * 7) + 19, contact['mobile_conf'])
                index += 1
            line += 1
        wb1.save('addresses.xls')
        result_file = open('addresses.xls', 'rb').read()

        # gcci_memberdirectory_extract_paperive the result tos the user
        msg = 'Save the File with '".xls"' extension.'
        addresses = base64.encodestring(result_file)
        
        ctx = self.env.context.copy()
        ctx.update({'msg':msg, 'addresses':addresses})
        view = self.env.ref('cci_memberdirectory.view_cci_memberdirectory_extract_paper_msg')
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.memberdirectory.extract.paper.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_memberdirectory_extract_paper_msg(models.TransientModel):
    _name = 'cci.memberdirectory.extract.paper.msg'
    
    msg = fields.Text(string='File created', readonly=True)
    addresses_xls = fields.Binary(string='Prepared file', readonly= True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_memberdirectory_extract_paper_msg, self).default_get(fields)
        if self.env.context.get('addresses'):
            rec['addresses_xls'] = self.env.context['addresses']
        if self.env.context.get('msg'):
            rec['msg'] = self.env.context['msg']
        return rec
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

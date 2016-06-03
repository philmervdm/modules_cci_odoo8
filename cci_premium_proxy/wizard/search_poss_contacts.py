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
from openerp import models, fields , api , _ 

class wizard_search_poss_contacts(models.TransientModel):
    _name = 'search.poss.contacts'
    
    @api.multi
    def search_poss_contacts(self):
        premium_contact_id = self.env.context.get('active_id') #data['id']
        premium_contact_obj = self.env['premium_contact']
        contact_obj = self.env['res.partner']
        job_obj = self.env['res.partner']
        premium_contact = premium_contact_obj.browse([premium_contact_id])[0]
        poss_contact_ids = []
        # search on name
        contact_ids = contact_obj.search([('name','=',premium_contact.last_name)])
        if contact_ids:
            poss_contact_ids.extend(contact_ids.ids)
        if premium_contact.mobile:
            # search on mobile in contact and jobs
            contact_ids = contact_obj.search([('mobile','=',premium_contact.mobile)])
            if contact_ids:
                poss_contact_ids.extend(contact_ids.ids)
            job_ids = job_obj.search([('phone','=',premium_contact.mobile)])
            if job_ids:
                jobs = job_ids.read(['contact_id'])
                for job in jobs:
                    if job['contact_id'] and job['contact_id'][0] not in poss_contact_ids:
                        poss_contact_ids.append(job['contact_id'][0])
                        
        if premium_contact.email:
            # search on emails in contact and jobs
            contact_ids = contact_obj.search([('email','=',premium_contact.email)])
            if contact_ids:
                poss_contact_ids.extend(contact_ids.ids)
            job_ids = job_obj.search([('email','=',premium_contact.email)])
            if job_ids:
                jobs = job_ids.read(['contact_id'])
                for job in jobs:
                    if job['contact_id'] and job['contact_id'][0] not in poss_contact_ids:
                        poss_contact_ids.append(job['contact_id'][0])
        value = {
            'domain': [('id', 'in', poss_contact_ids)],
            'name': 'Possible Contacts',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


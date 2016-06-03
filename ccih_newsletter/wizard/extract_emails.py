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
from openerp import models, fields ,api , _
import time
import datetime
import base64
from xlwt import *

class wizard_extract_emails(models.TransientModel):
    _name = 'wizard.extract.emails'

    addresses = fields.Boolean(string = 'Site email', default=True)
    contacts = fields.Boolean(string = 'Personal email')
    jobs = fields.Boolean(string = 'Functional email', default=True)
    explanation = fields.Text(string = 'Source', readonly=True,
                    default=u'''Cet outil extrait toutes les adresses mail des fonctions, adresses de siège et/ou fiches personnelles de tous les partenaires actifs.\n
                                Il ignore les emails en provenance de fonctions ou de fiches personnelles pour laquelle la personne de contact est indiquée comme 'jamais' ou 'désinscrit' dans le zone 'Envoi Alter Ego'.\n
                                Une même adresse email ne sera reprise qu'une seule fois dans le fichier final.''')
    
    
    @api.multi
    def get_file(self):
        # we search all unsubscribed email addresses
        obj_bounce = self.env['mail_bounce']
        bounced = []
        bounce_ids = obj_bounce.search([])
        if bounce_ids:
            bounces = bounce_ids.read(['name'])
            bounced = [x['name'].strip().lower() for x in bounces]
        # we will get all active partners, extract all job emails, while keeping all address email to add them later, without repetition
        obj_partner = self.env['res.partner']
        partners = obj_partner.search([('state_id','=',1)])
        wb1 = Workbook()
        ws1 = wb1.add_sheet('Emails')
        ws1.write(0,0,'partner_id')
        ws1.write(0,1,'address_id')
        ws1.write(0,2,'job_id')
        ws1.write(0,3,'contact_id')
        ws1.write(0,4,'email')
        ws1.write(0,5,'last_name')
        ws1.write(0,6,'first_name')
        ws1.write(0,7,'company_name')
        doubles = 0
        line = 1
        inserted_emails = []
        addr_emails = []
        cont_emails = []
        for partner in partners:
            for addr in partner.child_ids:
                if self.addresses and addr.email and addr.email.strip().lower() not in inserted_emails and addr.email.strip().lower() not in bounced:
                    addr_emails.append({'partner_id':partner.id,'address_id':addr.id,'email':addr.email.strip().lower(),'company_name':partner.name})
                
                if self.jobs and self.contacts:
                    for job in addr.other_contact_ids:
                        if job.email and job.contact_id and job.contact_id.alterego_subscribe not in ['never','unsubscribed']:
                            if not (job.email.strip().lower() in inserted_emails) and (job.email.strip().lower() not in bounced):
                                ws1.write(line,0,partner.id)
                                ws1.write(line,1,addr.id)
                                ws1.write(line,2,job.id)
                                ws1.write(line,3,job.contact_id.id)
                                ws1.write(line,4,job.email.strip().lower())
                                ws1.write(line,5,job.contact_id.name or '')
                                ws1.write(line,6,job.contact_id.first_name or '')
                                ws1.write(line,7,partner.name or '')
                                inserted_emails.append(job.email.strip().lower())
                                line += 1
                            else:
                                doubles += 1
                        
                        if self.contacts and job.contact_id and job.contact_id.email and job.contact_id.alterego_subscribe not in ['never','unsubscribed']:
                            if not (job.contact_id.email.strip().lower() in inserted_emails) and (job.contact_id.email.strip().lower() not in bounced):
                                cont_emails.append({'partner_id':partner.id,'address_id':addr.id,'job_id':job.id,'contact_id':job.contact_id.id,'email':job.contact_id.email.strip().lower(),
                                                    'company_name':partner.name,'contact_name':job.contact_id.name or '','contact_firstname':job.contact_id.first_name or ''})
        for email in addr_emails:
            if email['email'] not in inserted_emails:
                ws1.write(line,0,email['partner_id'])
                ws1.write(line,1,email['address_id'])
                ws1.write(line,2,0)
                ws1.write(line,3,0)
                ws1.write(line,4,email['email'])
                ws1.write(line,5,'')
                ws1.write(line,6,'')
                ws1.write(line,7,email['company_name'])
                inserted_emails.append(email['email'])
                line += 1
            else:
                doubles += 1
        for email in cont_emails:
            if email['email'] not in inserted_emails:
                ws1.write(line,0,email['partner_id'])
                ws1.write(line,1,email['address_id'])
                ws1.write(line,2,email['job_id'])
                ws1.write(line,3,email['contact_id'])
                ws1.write(line,4,email['email'])
                ws1.write(line,5,email['contact_name'])
                ws1.write(line,6,email['contact_firstname'])
                ws1.write(line,7,email['company_name'])
                inserted_emails.append(email['email'])
                line += 1
            else:
                doubles += 1
        wb1.save('newsletter.xls')
        result_file = open('newsletter.xls','rb').read()
        # give the result tos the user
        msg = u'Résultats : %i emails extraits (avec %i doublons éliminés)\n\nEnregistrez le fichier avec l\'extension \'.xls\'.' % (line-1,doubles)
        
        ctx = self.env.context.copy()
        ctx['msg'] = msg
        ctx['newsletter'] = base64.encodestring(result_file)
        return {
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'wizard.extract.emails.msg',
        'view_id': False,
        'type': 'ir.actions.act_window',
        'target': 'new',
        'context': ctx,
        }

class wizard_extract_emails_msg(models.TransientModel):
    _name = 'wizard.extract.emails.msg'
    
    name = fields.Char('Filename')
    msg = fields.Text(string = 'File created', readonly=True)
    newsletter = fields.Binary(string= u'Fichier préparé',readonly= True)
    
    @api.model
    def default_get(self,fields):
        res =  super(wizard_extract_emails_msg,self).default_get(fields)
        res['name'] = 'newsletter.xls'
        res['msg'] = self.env.context.get('msg')
        res['newsletter'] = self.env.context.get('newsletter')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


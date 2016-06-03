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
from openerp import models, fields, api , _
import time
import datetime
import base64
import StringIO
from xlwt import *

class wizard_unsubscribe_emails_csv(models.TransientModel):
    _name = 'wizard.unsubscribe.emails'
    
    explanation = fields.Text(string = 'Source', readonly=True,
                    default = u'''Cet outil récupère toutes les adresses emails d'un fichier CSV et marque les contacts liés à ces adresses emails comme 'désinscrit'.\n
                                Le fichier CSV DOIT avoir une colonne nommée 'email' contenant l'adresse email à radier et peut avoir une colonne 'reason' non obligatoire.\n
                                La première ligne du CSV DOIT être une ligne 'titre' avec les noms 'email' ou 'reason', ou toute autre nom. Mais seules les colonnes 'email' et éventuellement 'reason' seront traitées.''')
    
    field = fields.Selection( string = 'Field to correct', 
                              selection = [('rdp_subscribe','Abonnement Revue de Presse'),('agenda_subscribe','Abonnement Agenda'),('alterego_subscribe','Abonnement Alter Ego')],required=True)
    input = fields.Binary(string = 'Email to exclude file', required=True)
    
    @api.multi
    def unsubscribe_file(self):
        inputfile = self.input
        inputdata = StringIO.StringIO(base64.decodestring(inputfile))
        lines = inputdata.readlines()
        first_line = lines[0].replace('\n','').replace('\r','')
        separator = ';'
        only_one_column = False
        if len(first_line) == 5 and first_line == 'email':
            separator = ' ' # can't be empty...
            only_one_column = True
        else:
            if separator not in first_line:
                separator = ','
                if separator not in first_line:
                    if first_line == 'email':
                        separator = ';'
                    else:
                        separator = ','

        wb1 = Workbook()
        ws1 = wb1.add_sheet('Emails to Unsubscribe')
        ws1.write(0,0,'Date')
        ws1.write(0,1,datetime.date.today().strftime('%Y-%m-%d'))
        ws1.write(1,0,'Lines')
        ws1.write(1,1,len(lines)-1)
        ws1.write(2,0,'Separator')
        ws1.write(2,1,separator)
        current_line = 4
        if separator or only_one_column:
            count_ok = 0 
            count_ko = 0
            already_bounced = 0
            contact_marked = 0
            field_names = first_line.split(separator)
            if 'email' in field_names:

                ws1.write(current_line,0,'origin_email')
                ws1.write(current_line,1,'origin_reason')
                ws1.write(current_line,2,'problem')
                ws1.write(current_line,3,'contact_id')
                ws1.write(current_line,4,'contact name [address id]')
                ws1.write(current_line,5,'task')
                current_line += 1

                index_email = field_names.index('email')
                index_reason = 0
                if 'reason' in field_names:
                    index_reason = field_names.index('reason')
                obj_bounce = self.env['mail_bounce']
                obj_contact = self.env['res.partner']
                obj_job = self.env['res.partner']
                obj_address = self.env['res.partner']
                concerned_field = self.field
                corrected_contact_ids = []
                for line in lines[1:]:
                    line = line.replace('\n','')
                    elements = line.split(separator)
                    if len(elements) == len(field_names):
                        count_ok += 1
                        if index_reason:
                            reason = elements[index_reason].strip()
                        else:
                            reason = ''
                        searched_email = elements[index_email].strip()
                        bounce_ids = obj_bounce.search([('name','=',searched_email)])
                        if not bounce_ids:
                            obj_bounce.create({'name':searched_email,'date':datetime.date.today().strftime('%Y-%m-%d'),'type':reason})
                            found = 0
                            current_email_contact_ids = []
                            # search in contact
                            contact_ids = obj_contact.search([('email','=',searched_email)])
                            if contact_ids:
                                found += len(contact_ids)
                                ws1.write(current_line,0,searched_email)
                                ws1.write(current_line,1,reason)
                                ws1.write(current_line,2,'found')
                                current_line + 1
                                contacts = contact_ids.read([concerned_field,'id','name','first_name'])
                                for contact in contacts:
                                    current_email_contact_ids.append(contact['id'])
                                    ws1.write(current_line,3,contact['id'])
                                    ws1.write(current_line,4,contact['name'] + ' ' + ( contact['first_name'] or '' ) )
                                    if contact['id'] not in corrected_contact_ids:
                                        if contact[concerned_field] not in ['unsubscribed','never']:
                                            obj_contact.browse(contact['id']).write({concerned_field:'unsubscribed'})
                                            ws1.write(current_line,5,contact[concerned_field] + ' set to unsubscribed')
                                            corrected_contact_ids.append(contact['id'])
                                        else:
                                            ws1.write(current_line,5,'already ' + contact[concerned_field] + ' => unchanged')
                                    else:
                                        ws1.write(current_line,5,'already managed before in this file')
                                    current_line += 1
                            # search in jobs
                            job_ids = obj_job.search([('email','=',searched_email)])
                            if job_ids:
                                if found == 0:
                                    ws1.write(current_line,0,searched_email)
                                    ws1.write(current_line,1,reason)
                                    ws1.write(current_line,2,'found')
                                    current_line + 1
                                found += len(job_ids)
                                jobs = job_ids #obj_job.browse(cr,uid,job_ids)
                                for job in jobs:
                                    if job.contact_id and job.contact_id.id not in current_email_contact_ids:
                                        ws1.write(current_line,3,job.contact_id.id)
                                        ws1.write(current_line,4,job.contact_id.name + ' ' + ( job.contact_id.first_name or '' ) )
                                        if job.contact_id.id not in corrected_contact_ids:
                                            if eval('job.contact_id.'+concerned_field) not in ['unsubscribed','never']:
                                                obj_contact.write(cr,uid,[job.contact_id.id,],{concerned_field:'unsubscribed'})
                                                ws1.write(current_line,5,eval('job.contact_id.'+concerned_field) + ' set to unsubscribed')
                                                corrected_contact_ids.append(contact['id'])
                                                current_line += 1
                                            else:
                                                ws1.write(current_line,5,'already ' + eval('job.contact_id.'+concerned_field) + ' => unchanged')
                                                current_line += 1
                            # search in addresses
                            addr_ids = obj_address.search([('email','=',searched_email)])
                            if addr_ids:
                                if found == 0:
                                    ws1.write(current_line,0,searched_email)
                                    ws1.write(current_line,1,reason)
                                    ws1.write(current_line,2,'found')
                                    current_line + 1
                                found += len(addr_ids)
                                addrs = addr_ids.read(['id'])
                                for addr in addrs:
                                    ws1.write(current_line,3,'-')
                                    ws1.write(current_line,4,'[%i]' % addr['id'] )
                                    ws1.write(current_line,5,'email on address => manual management needed ...')
                                    current_line += 1
                            if found == 0:
                                ws1.write(current_line,0,searched_email)
                                ws1.write(current_line,1,reason)
                                ws1.write(current_line,2,'Not found in OpenERP')
                                current_line += 1
                        else:
                            # already_bounced = > do nothing else
                            already_bounced += 1
                            ws1.write(current_line,0,searched_email)
                            ws1.write(current_line,1,reason)
                            ws1.write(current_line,2,'already bounced => no more management')
                            current_line += 1
                    else:
                        print 'wrong number of elements'
                        count_ko += 1
                        ws1.write(current_line,0,searched_email)
                        ws1.write(current_line,1,reason)
                        ws1.write(current_line,2,'wrong number of element in the line %s' % line )
                        current_line += 1
                # give the result to the user
                msg=u'Résultats : %i managed lines and %i lines impossible to manage.\n%i contacts corrected.' % (count_ok,count_ko,len(corrected_contact_ids))
            else:
                msg=u'Aucune récupération : pas de champ email détecté. Or, ce champ est obligatoire...\nHeader : %s' % first_line
                ws1.write(current_line,0,'NO IMPORT : because no field with the header \'email\' has been found.')
                current_line += 1
                ws1.write(current_line,0,'Header')
                ws1.write(current_line,1,first_line)
                current_line += 1
        else:
            msg=u'Aucune récupération : impossible de détecter le caractère séparateur \';\' ou \',\' et l\'unique champ n\'est pas \'email\'...\nHeader : %s' % first_line
            ws1.write(current_line,0,'NO IMPORT : because no separator found; by default \';\' is perfect, but \',\' is managed also.')
            current_line += 1
            ws1.write(current_line,0,'Header')
            ws1.write(current_line,1,first_line)
            current_line += 1
        wb1.save('unsubscribed.xls')
        result_file = open('unsubscribed.xls','rb').read()

        ctx = self.env.context.copy()
        ctx['msg'] = msg
        ctx['unsubscribed'] = base64.encodestring(result_file)

        return {
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'wizard.unsubscribe.emails.msg',
        'view_id': False,
        'type': 'ir.actions.act_window',
        'target': 'new',
        'context': ctx,
        }

class wizard_unsubscribe_emails_msg(models.TransientModel):
    _name = 'wizard.unsubscribe.emails.msg'
    
    name = fields.Char('Filename')
    msg = fields.Text(string = 'File created', readonly=True)
    unsubscribed = fields.Binary(string= 'Prepared file',readonly= True)
    
    @api.model
    def default_get(self,fields):
        res =  super(wizard_unsubscribe_emails_msg,self).default_get(fields)
        res['name'] = 'unsubscribed.xls'
        res['msg'] = self.env.context.get('msg')
        res['unsubscribed'] = self.env.context.get('unsubscribed')
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


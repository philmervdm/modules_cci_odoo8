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
# 1.1 : add the salesman to each records
from openerp import models, fields , api , _
from openerp.exceptions import Warning

import datetime
import base64
import csv
import StringIO

CURRENT_PROSPECT = "Prospect en cours"
FUTURE_PROSPECT = "Prospect"
CLASSICAL_MEMBER = "Membre"

def compose_fullname(company_name,address_name):
    if company_name:
        if address_name:
            if address_name[0] == '-':
                result = company_name + ' ' + address_name
            elif address_name[0:1] == ' -':
                result = company_name + address_name
            else:
                result = address_name
        else:
            result = company_name
    else:
        # possible because can be a private address
        if address_name:
            result = address_name
        else:
            result = ''
    return result

def collect_new_prospects(self,hfCSV,file_size_limit,count_lines,sended_contacts,sended_addresses):
    # 1. return prospects of the last month as 'future' prospects
    obj_addr = self.env['res.partner']
    address_ids = obj_addr.search([('magazine_subscription_source','=',CURRENT_PROSPECT)])
    if address_ids:
        address_ids.write({'magazine_subscription_source':FUTURE_PROSPECT})
    #
    obj_job = self.env['res.partner']
    job_ids = obj_job.search([('magazine_subscription_source','=',CURRENT_PROSPECT)])
    if job_ids:
        job_ids.write({'magazine_subscription_source':FUTURE_PROSPECT})
    count_prospects = 0
    # collect all possible future prospects from address and job in one collection, sorted by 'magazine_lastsubscription'
    future_prospects = []
    addr_ids = obj_addr.search([('magazine_subscription','=','prospect'),('magazine_subscription_source','=',FUTURE_PROSPECT)])
    print 'len address ids'
    print len(addr_ids)
    addresses = addr_ids.read(['id','magazine_lastprospection','zip_id','notdelivered'])
    for addr in addresses:
        if addr['zip_id'] and ( not addr['notdelivered'] ) and ( not addr['id'] in sended_addresses ):
            future_prospects.append({'magazine_lastprospection':addr['magazine_lastprospection'] or '1900-01-01','type':'address','id':addr['id']})
    print 'len job ids'
    print len(job_ids)
    job_ids = obj_job.search([('magazine_subscription','=','prospect'),('magazine_subscription_source','=',FUTURE_PROSPECT)])
    jobs = job_ids.read(['id','magazine_lastprospection','contact_id'])
    for job in jobs:
        if job['contact_id'] and job['contact_id'][0] not in sended_contacts:
            future_prospects.append({'magazine_lastprospection':addr['magazine_lastprospection'] or '1900-01-01','type':'job','id':job['id']})
    newprospects = sorted(future_prospects, key=lambda x: x['magazine_lastprospection' ])
    print 'len new prospects'
    print len(newprospects)
    added_address_ids = []
    added_job_ids = []
    for prospect in newprospects:
        if count_lines >= file_size_limit:
            break
        if prospect['type'] == 'address':
            addr = obj_addr.browse(prospect['id'])
            if addr.zip_id and not addr.notdelivered and ( addr.id not in sended_addresses ):
                lContinue = True
                if addr.parent_id and ( addr.parent_id.state_id.id != 1 or addr.parent_id.membership_state in [('paid','free','invoiced')] ):
                    lContinue = False
                if lContinue: # either no partner (private address) or active partner
                    # not very optimal : a select in a loop, but, in reality, this case is rare
                    cr.execute('''
                            SELECT job.address_id as address_id, job.sequence_partner as sequence_partner, job.id as job_id, contact.id as contact_id,
                                   job.phone as phone, job.fax as fax, job.email as job_email, job.function_label as function_label, 
                                   job.function_code_label as function_code_label, job.magazine_subscription as magazine_subscription, 
                                   job.magazine_subscription_source as magazine_subscription_source, contact.name as name,  
                                   contact.first_name as first_name, contact.title as title, contact.mobile as mobile,
                                   contact.email as contact_email
                            FROM res_partner as job, res_partner as contact
                            WHERE job.contact_id = contact.id and job.active and contact.active and job.address_id = (%s)
                            ORDER by job.address_id, job.sequence_partner
                            ''' % str(prospect['id'])
                            )
                    result = self.env.cr.fetchall()
                    lJobCont = []
                    for rec in result:
                        lJobCont.append( {'address_id':rec[0],
                                       'sequence_partner':rec[1],
                                       'job_id':rec[2],
                                       'contact_id':rec[3],
                                       'phone':rec[4],
                                       'fax':rec[5],
                                       'job_email':rec[6],
                                       'function_label':rec[7],
                                       'function_code_label':rec[8],
                                       'magazine_subscription':rec[9],
                                       'magazine_subscription_source':rec[10],
                                       'name':rec[11],
                                       'first_name':rec[12],
                                       'title':rec[13],
                                       'mobile':rec[14],
                                       'contact_email':rec[15],
                                      })
                    current_job = False
                    for jobCont in lJobCont:
                        if ( '1' in ( jobCont['function_code_label'] or '' ) ) and ( jobCont['contact_id'] not in sended_contacts ):
                            current_job = jobCont
                            break
                    if not current_job:
                        for jobCont in lJobCont:
                            if ( 'G' in ( jobCont['function_code_label'] or '' ) ) and ( job['contact_id'] not in sended_contacts ):
                                current_job = jobCont
                                break
                    if not current_job:
                        for jobCont in lJobCont:
                            if jobCont['contact_id'] not in sended_contacts:
                                current_job = jobCont
                    record = []
                    if current_job:
                        record.append( ( current_job['first_name'] or '' ).encode('cp1252') )
                        record.append( ( current_job['name'] or '' ).encode('cp1252') )
                        record.append( ( current_job['title'] or '' ).encode('cp1252') )
                        record.append( ( current_job['contact_email'] or '' ).encode('cp1252') )
                        record.append( ( current_job['mobile'] or '' ).encode('cp1252') )
                        record.append( ( current_job['phone'] or '' ).encode('cp1252') )
                        record.append( ( current_job['fax'] or '' ).encode('cp1252') )
                        record.append( ( current_job['job_email'] or '' ).encode('cp1252') )
                        record.append( ( current_job['function_label'] or '' ).encode('cp1252') )
                        record.append( ( current_job['function_code_label'] or '' ).encode('cp1252') )
                    else:
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                    record.append( ( addr.type or '' ).encode('cp1252') )
                    if addr.name and addr.name[0] == '-':
                        record.append( ( ' ' + addr.name ).encode('cp1252') )
                    else:
                        record.append( ( addr.name or '' ).encode('cp1252') )
                    record.append( ( addr.street or '' ).encode('cp1252') )
                    record.append( ( addr.street2 or '' ).encode('cp1252') )
                    if addr.zip_id.name == 'manuel':
                        record.append( addr.zip_id.city.encode('cp1252') )
                    else:
                        record.append( ( addr.zip_id.name + ' ' + addr.zip_id.city ).encode('cp1252') )
                    record.append( ( addr.email or '' ).encode('cp1252') )
                    if addr.parent_id:
                        record.append( addr.parent_id.name.encode('cp1252') )
                        record.append( ( addr.parent_id.title and addr.parent_id.title.name or '' ).encode('cp1252') )
                        record.append( compose_fullname( addr.parent_id.name, addr.name ).encode('cp1252') )
                    else:
                        record.append( '' )
                        record.append( '' )
                        record.append( compose_fullname( '', addr.name ).encode('cp1252') )
                    if current_job:
                        record.append( current_job['contact_id'] )
                        record.append( current_job['job_id'] )
                    else:
                        record.append( 0 )
                        record.append( 0 )
                    record.append( addr.id )
                    if addr.partner_id:
                        record.append( addr.partner_id.id )
                    else:
                        record.append( 0 )
                    record.append( 'prospect' )
                    record.append( ( addr.magazine_subscription or '' ).encode('cp1252') )
                    record.append( ( addr.magazine_subscription_source or '' ).encode('cp1252') )
                    if current_job:
                        record.append( ( current_job['magazine_subscription'] or '' ).encode('cp1252') )
                        record.append( ( current_job['magazine_subscription_source'] or '' ).encode('cp1252') )
                    else:
                        record.append('')
                        record.append('')
                    if addr.parent_id and addr.parent_id.user_id:
                        record.append( addr.parent_id.user_id.name.encode('cp1252') )
                    else:
                        record.append('')
                    hfCSV.writerow( record )
                    count_lines += 1
                    count_prospects += 1
                    if current_job:
                        sended_contacts.append( current_job['contact_id'] )
                    sended_addresses.append( addr.id )
                    added_address_ids.append(prospect['id'])
        else: ## type = 'job'
            job = obj_job.read(prospect['id'],['id','contact_id','address_id','function_label','function_code_label','phone','email','fax','magazine_subscription','magazine_subscription_source'])
            if job['contact_id'] and ( job['contact_id'][0] not in sended_contacts ) and job['address_id'] and ( job['address_id'][0] not in sended_addresses ):
                contact = self.env['res.partner'].read(job['contact_id'][0],['id','name','first_name','title','mobile','email','active'])
                address = self.env['res.partner'].browse(job['address_id'][0])
                if contact['active'] and address.active and ( not address.notdelivered ) and address.zip_id:
                    # the contact person is OK and the address is valid 
                    lContinue = True
                    if address.partner_id and ( address.parent_id.state_id.id != 1 or address.parent_id.membership_state in [('paid','free','invoiced')] ):
                        lContinue = False
                    if lContinue: # either no partner (private address) or active partner
                        record = []
                        record.append( ( contact['first_name'] or '' ).encode('cp1252') )
                        record.append( ( contact['name'] or '' ).encode('cp1252') )
                        record.append( ( contact['title'] or '' ).encode('cp1252') )
                        record.append( ( contact['email'] or '' ).encode('cp1252') )
                        record.append( ( contact['mobile'] or '' ).encode('cp1252') )
                        record.append( ( job['phone'] or '' ).encode('cp1252') )
                        record.append( ( job['fax'] or '' ).encode('cp1252') )
                        record.append( ( job['email'] or '' ).encode('cp1252') )
                        record.append( ( job['function_label'] or '' ).encode('cp1252') )
                        record.append( ( job['function_code_label'] or '' ).encode('cp1252') )
                        record.append( ( address.type or '' ).encode('cp1252') )
                        if address.name and address.name[0] == '-':
                            record.append( ( ' ' + address.name ).encode('cp1252') )
                        else:
                            record.append( ( address.name or '' ).encode('cp1252') )
                        record.append( ( address.street or '' ).encode('cp1252') )
                        record.append( ( address.street2 or '' ).encode('cp1252') )
                        if address.zip_id.name == 'manuel':
                            record.append( address.zip_id.city.encode('cp1252') )
                        else:
                            record.append( ( address.zip_id.name + ' ' + address.zip_id.city ).encode('cp1252') )
                        record.append( ( address.email or '' ).encode('cp1252') )
                        if address.partner_id:
                            record.append( address.partner_id.name.encode('cp1252') )
                            record.append( ( address.partner_id.title or '' ).encode('cp1252') )
                            record.append( compose_fullname( address.partner_id.name, address.name ).encode('cp1252') )
                        else:
                            record.append( '' )
                            record.append( '' )
                            record.append( compose_fullname( '', address.name ).encode('cp1252') )
                        record.append( contact['id'] )
                        record.append( job['id'] )
                        record.append( address.id )
                        if address.parent_id:
                            record.append( address.parent_id.id )
                        else:
                            record.append( 0 )
                        record.append( 'prospect' )
                        record.append( ( address.magazine_subscription or '' ).encode('cp1252') )
                        record.append( ( address.magazine_subscription_source or '' ).encode('cp1252') )
                        record.append( ( job['magazine_subscription'] or '' ).encode('cp1252') )
                        record.append( ( job['magazine_subscription_source'] or '' ).encode('cp1252') )
                        if address.parent_id and address.parent_id.user_id:
                            record.append( address.parent_id.user_id.name.encode('cp1252') )
                        else:
                            record.append('')
                        hfCSV.writerow( record )
                        count_lines +=1
                        count_prospects += 1
                        sended_contacts.append( contact['id'] )
                        sended_addresses.append( address.id )
                        added_job_ids.append(prospect['id'])
    # record the sending to theses selected prospects
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if added_address_ids:
        added_address_ids.write({'magazine_subscription_source':CURRENT_PROSPECT,'magazine_lastprospection':today})
    if added_job_ids:
        added_job_ids.write({'magazine_subscription_source':CURRENT_PROSPECT,'magazine_lastprospection':today})
    return (count_lines,count_prospects)

def collect_same_prospects(cr,uid,hfCSV,count_lines,sended_contacts,sended_addresses):
    count_prospects = 0
    added_address_ids = []
    added_job_ids = []
    # extract the same prospects than the last month in addresses
    obj_addr = pooler.get_pool(cr.dbname).get('res.partner.address')
    addr_ids = obj_addr.search(cr,uid,[('magazine_subscription','=','prospect'),('magazine_subscription_source','=',CURRENT_PROSPECT)])
    if addr_ids:
        addresses = obj_addr.browse(cr,uid,addr_ids)
    else:
        addresses = []
    if addresses:
        cr.execute('''
                SELECT job.address_id as address_id, job.sequence_partner as sequence_partner, job.id as job_id, contact.id as contact_id,
                       job.phone as phone, job.fax as fax, job.email as job_email, job.function_label as function_label, 
                       job.function_code_label as function_code_label, job.magazine_subscription as magazine_subscription, 
                       job.magazine_subscription_source as magazine_subscription_source, contact.name as name,  
                       contact.first_name as first_name, contact.title as title, contact.mobile as mobile,
                       contact.email as contact_email
                FROM res_partner_job as job, res_partner_contact as contact
                WHERE job.contact_id = contact.id and job.active and contact.active and job.address_id IN (%s)
                ORDER by job.address_id, job.sequence_partner
                ''' % ','.join([str(id) for id in addr_ids])
                )
        result = cr.fetchall()
        dJobCont = {}
        last_address_id = 0
        for rec in result:
            if rec[0] != last_address_id:
                if last_address_id > 0:
                    dJobCont[last_address_id] = lJobs
                last_address_id = rec[0]
                lJobs = []
            lJobs.append( {'address_id':rec[0],
                           'sequence_partner':rec[1],
                           'job_id':rec[2],
                           'contact_id':rec[3],
                           'phone':rec[4],
                           'fax':rec[5],
                           'job_email':rec[6],
                           'function_label':rec[7],
                           'function_code_label':rec[8],
                           'magazine_subscription':rec[9],
                           'magazine_subscription_source':rec[10],
                           'name':rec[11],
                           'first_name':rec[12],
                           'title':rec[13],
                           'mobile':rec[14],
                           'contact_email':rec[15],
                          })
        if last_address_id > 0:
            dJobCont[last_address_id] = lJobs
        for addr in addresses:
            if addr.zip_id and not addr.notdelivered and ( addr.id not in sended_addresses ):
                lContinue = True
                if addr.partner_id and addr.partner_id.state_id.id != 1 and addr.partner_id.membership_state not in [('paid','free','invoiced')]:
                    lContinue = False
                if lContinue: # either no partner (private address) or active partner
                    current_job = False
                    if dJobCont.has_key( addr.id ):
                        lJobCont = dJobCont[ addr.id ]
                        for jobCont in lJobCont:
                            if ( '1' in ( jobCont['function_code_label'] or '' ) ) and ( jobCont['contact_id'] not in sended_contacts ):
                                current_job = jobCont
                                break
                        if not current_job:
                            for jobCont in lJobCont:
                                if ( 'G' in ( jobCont['function_code_label'] or '' ) ) and ( jobCont['contact_id'] not in sended_contacts ):
                                    current_job = jobCont
                                    break
                        if not current_job:
                            for jobCont in lJobCont:
                                if jobCont['contact_id'] not in sended_contacts:
                                    current_job = jobCont
                    record = []
                    if current_job:
                        record.append( ( current_job['first_name'] or '' ).encode('cp1252') )
                        record.append( ( current_job['name'] or '' ).encode('cp1252') )
                        record.append( ( current_job['title'] or '' ).encode('cp1252') )
                        record.append( ( current_job['contact_email'] or '' ).encode('cp1252') )
                        record.append( ( current_job['mobile'] or '' ).encode('cp1252') )
                        record.append( ( current_job['phone'] or '' ).encode('cp1252') )
                        record.append( ( current_job['fax'] or '' ).encode('cp1252') )
                        record.append( ( current_job['job_email'] or '' ).encode('cp1252') )
                        record.append( ( current_job['function_label'] or '' ).encode('cp1252') )
                        record.append( ( current_job['function_code_label'] or '' ).encode('cp1252') )
                    else:
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                        record.append( '' )
                    record.append( ( addr.type or '' ).encode('cp1252') )
                    if addr.name and addr.name[0] == '-':
                        record.append( ( ' ' + addr.name ).encode('cp1252') )
                    else:
                        record.append( ( addr.name or '' ).encode('cp1252') )
                    record.append( ( addr.street or '' ).encode('cp1252') )
                    record.append( ( addr.street2 or '' ).encode('cp1252') )
                    if addr.zip_id.name == 'manuel':
                        record.append( addr.zip_id.city.encode('cp1252') )
                    else:
                        record.append( ( addr.zip_id.name + ' ' + addr.zip_id.city ).encode('cp1252') )
                    record.append( ( addr.email or '' ).encode('cp1252') )
                    if addr.partner_id:
                        record.append( addr.partner_id.name.encode('cp1252') )
                        record.append( ( addr.partner_id.title or '' ).encode('cp1252') )
                        record.append( compose_fullname( addr.partner_id.name, addr.name ).encode('cp1252') )
                    else:
                        record.append( '' )
                        record.append( '' )
                        record.append( compose_fullname( '', addr.name ).encode('cp1252') )
                    if current_job:
                        record.append( current_job['contact_id'] )
                        record.append( current_job['job_id'] )
                    else:
                        record.append( 0 )
                        record.append( 0 )
                    record.append( addr.id )
                    if addr.partner_id:
                        record.append( addr.partner_id.id )
                    else:
                        record.append( 0 )
                    record.append( 'addr_subscription' )
                    record.append( ( addr.magazine_subscription or '' ).encode('cp1252') )
                    record.append( ( addr.magazine_subscription_source or '' ).encode('cp1252') )
                    if current_job:
                        record.append( ( current_job['magazine_subscription'] or '' ).encode('cp1252') )
                        record.append( ( current_job['magazine_subscription_source'] or '' ).encode('cp1252') )
                    else:
                        record.append('')
                        record.append('')
                    if addr.partner_id and addr.partner_id.user_id:
                        record.append( addr.partner_id.user_id.name.encode('cp1252') )
                    else:
                        record.append('')
                    hfCSV.writerow( record )
                    count_lines += 1
                    count_prospects += 1
                    added_address_ids.append( addr.id )
                    if current_job:
                        sended_contacts.append( current_job['contact_id'] )
                    sended_addresses.append( addr.id )
    # extract the same prospects than the last month in jobs
    obj_job = pooler.get_pool(cr.dbname).get('res.partner.job')
    job_ids = obj_job.search(cr,uid,[('magazine_subscription','=','prospect'),('magazine_subscription_source','=',CURRENT_PROSPECT)])
    if job_ids:
        jobs = obj_job.read(cr,uid,job_ids,['id','contact_id','address_id','function_label','function_code_label','phone','email','fax','magazine_subscription','magazine_subscription_source'])
    else:
        jobs = []
    contact_ids = []
    address_ids = []
    for job in jobs:
        if job['contact_id']:
            contact_ids.append( job['contact_id'][0] )
        if job['address_id']:
            address_ids.append( job['address_id'][0] )
    contacts = pooler.get_pool(cr.dbname).get('res.partner.contact').read(cr,uid,contact_ids,['id','name','first_name','title','mobile','email','active'])
    dConts = {}
    for cont in contacts:
        dConts[cont['id']] = cont
    addresses = pooler.get_pool(cr.dbname).get('res.partner.address').browse(cr,uid,address_ids)
    dAddr = {}
    for addr in addresses:
        dAddr[addr.id] = addr
    for job in jobs:
        if job['contact_id'] and ( job['contact_id'][0] not in sended_contacts ) and dConts.has_key(job['contact_id'][0] ) \
                             and job['address_id'] and dAddr.has_key(job['address_id'][0]):
            contact = dConts[job['contact_id'][0]]
            address = dAddr[job['address_id'][0]]
            if contact['active'] and address.active and ( not address.notdelivered ) and address.zip_id:
                # the contact person is OK and the address is valid 
                lContinue = True
                if address.partner_id and address.partner_id.state_id.id != 1 and address.partner_id.membership_state not in [('paid','free','invoiced')]:
                    lContinue = False
                if lContinue: # either no partner (private address) or active partner
                    record = []
                    record.append( ( contact['first_name'] or '' ).encode('cp1252') )
                    record.append( ( contact['name'] or '' ).encode('cp1252') )
                    record.append( ( contact['title'] or '' ).encode('cp1252') )
                    record.append( ( contact['email'] or '' ).encode('cp1252') )
                    record.append( ( contact['mobile'] or '' ).encode('cp1252') )
                    record.append( ( job['phone'] or '' ).encode('cp1252') )
                    record.append( ( job['fax'] or '' ).encode('cp1252') )
                    record.append( ( job['email'] or '' ).encode('cp1252') )
                    record.append( ( job['function_label'] or '' ).encode('cp1252') )
                    record.append( ( job['function_code_label'] or '' ).encode('cp1252') )
                    record.append( ( address.type or '' ).encode('cp1252') )
                    if address.name and address.name[0] == '-':
                        record.append( ( ' ' + address.name ).encode('cp1252') )
                    else:
                        record.append( ( address.name or '' ).encode('cp1252') )
                    record.append( ( address.street or '' ).encode('cp1252') )
                    record.append( ( address.street2 or '' ).encode('cp1252') )
                    if address.zip_id.name == 'manuel':
                        record.append( address.zip_id.city.encode('cp1252') )
                    else:
                        record.append( ( address.zip_id.name + ' ' + address.zip_id.city ).encode('cp1252') )
                    record.append( ( address.email or '' ).encode('cp1252') )
                    if address.partner_id:
                        record.append( address.partner_id.name.encode('cp1252') )
                        record.append( ( address.partner_id.title or '' ).encode('cp1252') )
                        record.append( compose_fullname( address.partner_id.name, address.name ).encode('cp1252') )
                    else:
                        record.append( '' )
                        record.append( '' )
                        record.append( compose_fullname( '', address.name ).encode('cp1252') )
                    record.append( contact['id'] )
                    record.append( job['id'] )
                    record.append( address.id )
                    if address.partner_id:
                        record.append( address.partner_id.id )
                    else:
                        record.append( 0 )
                    record.append( 'job_subscription' )
                    record.append( ( address.magazine_subscription or '' ).encode('cp1252') )
                    record.append( ( address.magazine_subscription_source or '' ).encode('cp1252') )
                    record.append( ( job['magazine_subscription'] or '' ).encode('cp1252') )
                    record.append( ( job['magazine_subscription_source'] or '' ).encode('cp1252') )
                    if address.partner_id and address.partner_id.user_id:
                        record.append( address.partner_id.user_id.name.encode('cp1252') )
                    else:
                        record.append('')
                    hfCSV.writerow( record )
                    count_lines += 1
                    count_prospects += 1
                    added_job_ids.append( job['id'] )
                    sended_contacts.append( contact['id'] )
                    sended_addresses.append( address.id )

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if added_address_ids:
        obj_addr.write(cr,uid,added_address_ids,{'magazine_lastprospection':today})
    if added_job_ids:
        obj_job.write(cr,uid,added_job_ids,{'magazine_lastprospection':today})
    return (count_lines,count_prospects)

class wizard_get_ppi(models.Model):

    _name = 'wizard.get.ppi'
    
    method = fields.Selection(string = 'Method', selection = [('cciconnect','CCI Connect standard'),('ccih','CCIH standard')], required = True, default = 'cciconnect')
    prospect_limit = fields.Integer(string = 'Limit')
    
    @api.multi
    def extract_file(self):
        if self.method == 'cciconnect':
            self._extract_cciconnect()
        elif self.method == 'ccih':
            self._extract_ccih()
        return True

    @api.multi
    def _extract_cciconnect(self):
        try: ### to capture the possible error of transcripting caracters to cp1252
            ctx = self.env.context.copy()
            count_lines = 0  ## count the number of lines in the finale file to show to the user
            count_prospects = 0 ## count the number of prospects incorporated in the final file
            sended_contacts = []  ## list of id of contacts in the final file. The same id can't exists two times
            sended_addresses = [] ## list of id of addresses in the final file. Possible, under certains circumstances, that an id exists several times if this list
            
            ifile=StringIO.StringIO()
            hfCSV = csv.writer(ifile,delimiter=";",quotechar='"',quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n')
            hfCSV.writerow(['firstname','lastname','courtesy','persoemail','mobile','profphone','proffax','profemail','function',
                            'function_codes','adrtype','adrname','adrstreet','adrstreet2','adrcity','adremail','company','company_legal','name',
                            'contact_id','job_id','address_id','partner_id','origin','addr_magazine_subscription','addr_magazine_source',
                            'job_magazine_subscription','job_magazine_source','salesman'])

            # step 1. Extract the job
            obj_job = self.env['res.partner']
            jobs = obj_job.search([('magazine_subscription','=','personal')])
            # the following code doesn't work because the browse try to read a 'name' column that doesn't exist on res.partner.job
            for job in jobs:
                if job.contact_id and job.address_id:
                    if ( job.contact_id.id not in sended_contacts ) and ( job.contact_id.active ) and \
                       ( job.address_id.active ) and ( not job.address_id.notdelivered ) and job.address_id.zip_id.id:
                        # the contact person is OK and the address is valid 
                        lContinue = True
                        if job.address_id.parent_id and job.address_id.parent_id.state_id.id != 1:
                            lContinue = False
                        if lContinue: # either no partner (private address) or active partner
                            record = []
                            record.append( ( job.contact_id.first_name or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.name or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.title and job.contact_id.title.name or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.email or '' ).encode('cp1252') )
                            record.append( ( job.contact_id.mobile or '' ).encode('cp1252') )
                            record.append( ( job.phone or '' ).encode('cp1252') )
                            record.append( ( job.fax or '' ).encode('cp1252') )
                            record.append( ( job.email or '' ).encode('cp1252') )
                            record.append( ( job.function_label or '' ).encode('cp1252') )
                            record.append( ( job.function_label_code or '' ).encode('cp1252') )
                            if job.address_id.name and job.address_id.name[0] == '-':
                                record.append( ( ' ' + job.address_id.name ).encode('cp1252') )
                            else:
                                record.append( ( job.address_id.name or '' ).encode('cp1252') )
                            record.append( ( job.address_id.street or '' ).encode('cp1252') )
                            record.append( ( job.address_id.street2 or '' ).encode('cp1252') )
                            if job.address_id.zip_id.name == 'manuel':
                                record.append( job.address_id.zip_id.city.encode('cp1252') )
                            else:
                                record.append( ( job.address_id.zip_id.name + ' ' + job.address_id.zip_id.city ).encode('cp1252') )
                            record.append( ( job.address_id.email or '' ).encode('cp1252') )
                            if job.address_id.parent_id:
                                record.append( job.address_id.parent_id.name.encode('cp1252') )
                                record.append( ( job.address_id.parent_id.title and job.address_id.parent_id.title.name or '' ).encode('cp1252') )
                                record.append( compose_fullname( job.address_id.parent_id.name, job.address_id.name ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                                record.append( compose_fullname( '', job.address_id.name ).encode('cp1252') )
                            record.append( job.contact_id.id )
                            record.append( job.id )
                            record.append( job.address_id.id )
                            if job.address_id.parent_id:
                                record.append( job.address_id.parent_id.id )
                            else:
                                record.append( 0 )
                            record.append( 'job_subscription' )
                            record.append( ( job.address_id.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( job.address_id.magazine_subscription_source or '' ).encode('cp1252') )
                            record.append( ( job.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( job.magazine_subscription_source or '' ).encode('cp1252') )
                            count_lines += 1
                            sended_contacts.append( job.contact_id.id )
                            sended_addresses.append( job.address_id.id )
            if jobs:
                jobs = jobs.read(['id','contact_id','address_id','function_label','function_code_label','phone','email','fax','magazine_subscription','magazine_subscription_source'])
            else:
                jobs = []
                
            contact_ids = []
            address_ids = []
            for job in jobs:
                if job['contact_id']:
                    contact_ids.append( job['contact_id'][0] )
                if job['address_id']:
                    address_ids.append( job['address_id'][0] )
                    
            contacts = self.env['res.partner'].read(contact_ids,['id','name','first_name','title','mobile','email','active'])
            dConts = {}
            for cont in contacts:
                dConts[cont['id']] = cont
            addresses = self.env['res.partner'].browse(address_ids)
            dAddr = {}
            for addr in addresses:
                dAddr[addr.id] = addr
                
            for job in jobs:
                if job['contact_id'] and ( job['contact_id'][0] not in sended_contacts ) and dConts.has_key(job['contact_id'][0] ) \
                                     and job['address_id'] and dAddr.has_key(job['address_id'][0]):
                    contact = dConts[job['contact_id'][0]]
                    address = dAddr[job['address_id'][0]]
                    if contact['active'] and address.active and ( not address.notdelivered ) and address.zip_id:
                        # the contact person is OK and the address is valid 
                        lContinue = True
                        if address.parent_id and address.parent_id.state_id.id != 1:
                            lContinue = False
                        else:
                            if address.parent_id and job['magazine_subscription_source'] == CLASSICAL_MEMBER and address.parent_id.membership_state not in ['paid','free','invoiced']:
                                lContinue = False
                        if lContinue: # either no partner (private address) or active partner
                            record = []
                            record.append( ( contact['first_name'] or '' ).encode('cp1252') )
                            record.append( ( contact['name'] or '' ).encode('cp1252') )
                            record.append( ( contact['title'] or '' ).encode('cp1252') )
                            record.append( ( contact['email'] or '' ).encode('cp1252') )
                            record.append( ( contact['mobile'] or '' ).encode('cp1252') )
                            record.append( ( job['phone'] or '' ).encode('cp1252') )
                            record.append( ( job['fax'] or '' ).encode('cp1252') )
                            record.append( ( job['email'] or '' ).encode('cp1252') )
                            record.append( ( job['function_label'] or '' ).encode('cp1252') )
                            record.append( ( job['function_code_label'] or '' ).encode('cp1252') )
                            record.append( ( address.type or '' ).encode('cp1252') )
                            if address.name and address.name[0] == '-':
                                record.append( ( ' ' + address.name ).encode('cp1252') )
                            else:
                                record.append( ( address.name or '' ).encode('cp1252') )
                            record.append( ( address.street or '' ).encode('cp1252') )
                            record.append( ( address.street2 or '' ).encode('cp1252') )
                            if address.zip_id.name == 'manuel':
                                record.append( address.zip_id.city.encode('cp1252') )
                            else:
                                record.append( ( address.zip_id.name + ' ' + address.zip_id.city ).encode('cp1252') )
                            record.append( ( address.email or '' ).encode('cp1252') )
                            if address.parent_id:
                                record.append( address.parent_id.name.encode('cp1252') )
                                record.append( ( address.parent_id.title and address.parent_id.title.name or '' ).encode('cp1252') )
                                record.append( compose_fullname( address.parent_id.name, address.name ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                                record.append( compose_fullname( '', address.name ).encode('cp1252') )
                            record.append( contact['id'] )
                            record.append( job['id'] )
                            record.append( address.id )
                            if address.partner_id:
                                record.append( address.parent_id.id )
                            else:
                                record.append( 0 )
                            record.append( 'job_subscription' )
                            record.append( ( address.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( address.magazine_subscription_source or '' ).encode('cp1252') )
                            record.append( ( job['magazine_subscription'] or '' ).encode('cp1252') )
                            record.append( ( job['magazine_subscription_source'] or '' ).encode('cp1252') )
                            if address.parent_id and address.parent_id.user_id:
                                record.append( address.parent_id.user_id.name.encode('cp1252') )
                            else:
                                record.append('')
                            hfCSV.writerow( record )
                            count_lines += 1
                            sended_contacts.append( contact['id'] )
                            sended_addresses.append( address.id )

            # step 2. Extract the addresses
            obj_addr = self.env['res.partner']
            addresses = obj_addr.search([('magazine_subscription','=','personal')])
#             if addr_ids:
#                 addresses = obj_addr.browse(cr,uid,addr_ids)
#             else:
#                 addresses = []
            if addresses:
                self.env.cr.execute('''
                        SELECT job.address_id as address_id, job.sequence_partner as sequence_partner, job.id as job_id, contact.id as contact_id,
                               job.phone as phone, job.fax as fax, job.email as job_email, job.function_label as function_label, 
                               job.function_code_label as function_code_label, job.magazine_subscription as magazine_subscription, 
                               job.magazine_subscription_source as magazine_subscription_source, contact.name as name,  
                               contact.first_name as first_name, contact.title as title, contact.mobile as mobile,
                               contact.email as contact_email
                        FROM res_partner as job, res_partner as contact
                        WHERE job.contact_id = contact.id and job.active and contact.active and job.address_id IN (%s)
                        ORDER by job.address_id, job.sequence_partner
                        ''' % ','.join([str(id) for id in addr_ids])
                        )
                result = self.env.cr.fetchall()
                dJobCont = {}
                last_address_id = 0
                for rec in result:
                    if rec[0] != last_address_id:
                        if last_address_id > 0:
                            dJobCont[last_address_id] = lJobs
                        last_address_id = rec[0]
                        lJobs = []
                        
                    lJobs.append( {'address_id':rec[0],
                                   'sequence_partner':rec[1],
                                   'job_id':rec[2],
                                   'contact_id':rec[3],
                                   'phone':rec[4],
                                   'fax':rec[5],
                                   'job_email':rec[6],
                                   'function_label':rec[7],
                                   'function_code_label':rec[8],
                                   'magazine_subscription':rec[9],
                                   'magazine_subscription_source':rec[10],
                                   'name':rec[11],
                                   'first_name':rec[12],
                                   'title':rec[13],
                                   'mobile':rec[14],
                                   'contact_email':rec[15],
                                  })
                if last_address_id > 0:
                    dJobCont[last_address_id] = lJobs
                for addr in addresses:
                    if addr.zip_id and not addr.notdelivered and ( addr.id not in sended_addresses ):
                        lContinue = True
                        if addr.parent_id and addr.parent_id.state_id.id != 1:
                            lContinue = False
                        if lContinue: # either no partner (private address) or active partner
#                              the following code doesn't work because the browse try to read a 'name' column that doesn't exist on res.partner.job
#                              we search for the first '1' of the first 'G' or the first one in the partner_sequenced order
                            current_job = False
                            if address.other_contact_ids:
                                current_sequence = 999999
                                for job in address.other_contact_ids:
                                    if ( '1' in ( job.function_code_label or '' ) ) and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                        if job.partner_sequence < current_sequence:
                                            current_job = job
                                            current_sequence = job.partner_sequence
                                if not current_job:
                                    for job in address.other_contact_ids:
                                        if ( 'G' in ( job.function_code_label or '' ) ) and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                            if job.partner_sequence < current_sequence:
                                                current_job = job
                                                current_sequence = job.partner_sequence
                                if not current_job:
                                    for job in address.other_contact_ids:
                                        if job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                            if job.partner_sequence < current_sequence:
                                                current_job = job
                                                current_sequence = job.partner_sequence
                            record = []
                            if current_job:
                                record.append( ( current_job.contact_id.first_name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.title and current_job.contact_id.title.name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.email or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.mobile or '' ).encode('cp1252') )
                                record.append( ( current_job.phone or '' ).encode('cp1252') )
                                record.append( ( current_job.fax or '' ).encode('cp1252') )
                                record.append( ( current_job.email or '' ).encode('cp1252') )
                                record.append( ( current_job.function_label or '' ).encode('cp1252') )
                                record.append( ( current_job.function_label_code or '' ).encode('cp1252') )
                                if addr.name and addr.name[0] == '-':
                                    record.append( ( ' ' + addr.name ).encode('cp1252') )
                                else:
                                    record.append( ( addr.name or '' ).encode('cp1252') )
                                record.append( ( addr.street or '' ).encode('cp1252') )
                                record.append( ( addr.street2 or '' ).encode('cp1252') )
                                if addr.zip_id.name == 'manuel':
                                    record.append( addr.zip_id.city.encode('cp1252') )
                                else:
                                    record.append( ( addr.zip_id.name + ' ' + addr.zip_id.city ).encode('cp1252') )
                                record.append( ( addr.email or '' ).encode('cp1252') )
                                if addr.parent_id:
                                    record.append( addr.parent_id.name.encode('cp1252') )
                                    record.append( ( addr.parent_id.title or '' ).encode('cp1252') )
                                    record.append( compose_fullname( addr.parent_id.name, addr.name ).encode('cp1252') )
                                else:
                                    record.append( '' )
                                    record.append( '' )
                                    record.append( compose_fullname( '', addr.name ).encode('cp1252') )
                                record.append( current_job.contact_id.id )
                                record.append( current_job.id )
                                record.append( addr.id )
                                if addr.partner_id:
                                    record.append( addr.parent_id.id )
                                else:
                                    record.append( 0 )
                                record.append( 'addr_subscription' )
                                record.append( ( addr.magazine_subscription or '' ).encode('cp1252') )
                                record.append( ( addr.magazine_subscription_source or '' ).encode('cp1252') )
                                record.append( ( current_job.magazine_subscription or '' ).encode('cp1252') )
                                record.append( ( current_job.magazine_subscription_source or '' ).encode('cp1252') )
                                count_lines += 1
                                sended_contacts.append( job.contact_id.id )
                                sended_addresses.append( addr.id )
                                
                            current_job = False
                            if dJobCont.has_key( addr.id ):
                                lJobCont = dJobCont[ addr.id ]
                                for jobCont in lJobCont:
                                    if ( '1' in ( jobCont['function_code_label'] or '' ) ) and ( jobCont['contact_id'] not in sended_contacts ):
                                        current_job = jobCont
                                        break
                                if not current_job:
                                    for jobCont in lJobCont:
                                        if ( 'G' in ( jobCont['function_code_label'] or '' ) ) and ( job['contact_id'] not in sended_contacts ):
                                            current_job = jobCont
                                            break
                                if not current_job:
                                    for jobCont in lJobCont:
                                        if jobCont['contact_id'] not in sended_contacts:
                                            current_job = jobCont
                            record = []
                            if current_job:
                                record.append( ( current_job['first_name'] or '' ).encode('cp1252') )
                                record.append( ( current_job['name'] or '' ).encode('cp1252') )
                                record.append( ( current_job['title'] or '' ).encode('cp1252') )
                                record.append( ( current_job['contact_email'] or '' ).encode('cp1252') )
                                record.append( ( current_job['mobile'] or '' ).encode('cp1252') )
                                record.append( ( current_job['phone'] or '' ).encode('cp1252') )
                                record.append( ( current_job['fax'] or '' ).encode('cp1252') )
                                record.append( ( current_job['job_email'] or '' ).encode('cp1252') )
                                record.append( ( current_job['function_label'] or '' ).encode('cp1252') )
                                record.append( ( current_job['function_code_label'] or '' ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                            record.append( ( addr.type or '' ).encode('cp1252') )
                            if addr.name and addr.name[0] == '-':
                                record.append( ( ' ' + addr.name ).encode('cp1252') )
                            else:
                                record.append( ( addr.name or '' ).encode('cp1252') )
                            record.append( ( addr.street or '' ).encode('cp1252') )
                            record.append( ( addr.street2 or '' ).encode('cp1252') )
                            if addr.zip_id.name == 'manuel':
                                record.append( addr.zip_id.city.encode('cp1252') )
                            else:
                                record.append( ( addr.zip_id.name + ' ' + addr.zip_id.city ).encode('cp1252') )
                            record.append( ( addr.email or '' ).encode('cp1252') )
                            if addr.parent_id:
                                record.append( addr.parent_id.name.encode('cp1252') )
                                record.append( ( addr.parent_id.title and addr.parent_id.title.name or '' ).encode('cp1252') )
                                record.append( compose_fullname( addr.parent_id.name, addr.name ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                                record.append( compose_fullname( '', addr.name ).encode('cp1252') )
                            if current_job:
                                record.append( current_job['contact_id'] )
                                record.append( current_job['job_id'] )
                            else:
                                record.append( 0 )
                                record.append( 0 )
                            record.append( addr.id )
                            if addr.partner_id:
                                record.append( addr.parent_id.id )
                            else:
                                record.append( 0 )
                            record.append( 'addr_subscription' )
                            record.append( ( addr.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( addr.magazine_subscription_source or '' ).encode('cp1252') )
                            if current_job:
                                record.append( ( current_job['magazine_subscription'] or '' ).encode('cp1252') )
                                record.append( ( current_job['magazine_subscription_source'] or '' ).encode('cp1252') )
                            else:
                                record.append('')
                                record.append('')
                            if addr.parent_id and addr.parent_id.user_id:
                                record.append( addr.parent_id.user_id.name.encode('cp1252') )
                            else:
                                record.append('')
                            hfCSV.writerow( record )
                            count_lines += 1
                            if current_job:
                                sended_contacts.append( current_job['contact_id'] )
                            sended_addresses.append( addr.id )

            # step 3. Extract the members not subscribed 'postal' and not yet sended
            obj_partner = self.env['res.partner']
            partners = obj_partner.search([('membership_state','in',['paid','invoiced']),('state_id','=',1)])
            if partners:
                addr_ids = []
                for part in partners:
                    for addr in part.child_ids:
                        addr_ids.append( addr.id )
                self.env.cr.execute('''
                        SELECT job.address_id as address_id, job.sequence_partner as sequence_partner, job.id as job_id, contact.id as contact_id,
                               job.phone as phone, job.fax as fax, job.email as job_email, job.function_label as function_label, 
                               job.function_code_label as function_code_label, job.magazine_subscription as magazine_subscription, 
                               job.magazine_subscription_source as magazine_subscription_source, contact.name as name,  
                               contact.first_name as first_name, contact.title as title, contact.mobile as mobile,
                               contact.email as contact_email
                        FROM res_partner as job, res_partner as contact
                        WHERE job.contact_id = contact.id and job.active and contact.active and job.address_id IN (%s)
                        ORDER by job.address_id, job.sequence_partner
                        ''' % ','.join([str(id) for id in addr_ids])
                        )
                result = self.env.cr.fetchall()
                dJobCont = {}
                last_address_id = 0
                for rec in result:
                    if rec[0] != last_address_id:
                        if last_address_id > 0:
                            dJobCont[last_address_id] = lJobs
                        last_address_id = rec[0]
                        lJobs = []
                    lJobs.append( {'address_id':rec[0],
                                   'sequence_partner':rec[1],
                                   'job_id':rec[2],
                                   'contact_id':rec[3],
                                   'phone':rec[4],
                                   'fax':rec[5],
                                   'job_email':rec[6],
                                   'function_label':rec[7],
                                   'function_code_label':rec[8],
                                   'magazine_subscription':rec[9],
                                   'magazine_subscription_source':rec[10],
                                   'name':rec[11],
                                   'first_name':rec[12],
                                   'title':rec[13],
                                   'mobile':rec[14],
                                   'contact_email':rec[15],
                                  })
                if last_address_id > 0:
                    dJobCont[last_address_id] = lJobs
            for partner in partners:
                if partner.child_ids:

                    # the following code doesn't work because the browse try to read a 'name' column that doesn't exist on res.partner.job
                    foundPostal = False
                    for addr in partner.child_ids:
                        if ( addr.magazine_subscription == 'postal' and addr.zip_id and addr.active and not addr.notdelivered ) or ( addr.id in sended_addresses ):
                            foundPostal = True
                            break;
                            for job in addr.other_contact_ids:
                                if job.magazine_subscription == 'postal' and job.active and job.contact_id and job.contact_id.active:
                                   foundPostal = True
                                   break
                    if not foundPostal:
                        # we search for the first usable address
                        current_address = False
                        for addr in partner.child_ids:
                            if address.type == 'default' and address.zip_id and address.active and not address.notdelivered:
                                current_address = address
                                break
                        if not current_address:
                            for addr in partner.child_ids:
                                if address.type == 'invoice' and address.zip_id and address.active and not address.notdelivered:
                                    current_address = address
                                    break
                        if not current_address:
                            current_sequence = 99999
                            for addr in partner.child_ids:
                                if ( address.type not in ['default','invoice'] ) and address.zip_id and address.active and not address.notdelivered:
                                    if address.sequence_partner < current_sequence:
                                        current_address = address
                                        current_sequence = address.sequence_partner
                        if current_address:
                            current_job = False
                            if current_address.other_contact_ids:
                                current_sequence = 999999
                                for job in current_address.other_contact_ids:
                                    print job.function_code_label
                                    print job.contact_id
                                    print job.contact_id.active
                                    if ( '1' in ( job.function_code_label or '' ) ) and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                        if job.partner_sequence < current_sequence:
                                            current_job = job
                                            current_sequence = job.partner_sequence
                                if not current_job:
                                    for job in current_address.job_ids:
                                        if ( 'G' in ( job.function_code_label or '' ) ) and job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                            if job.partner_sequence < current_sequence:
                                                current_job = job
                                                current_sequence = job.partner_sequence
                                if not current_job:
                                    for job in current_address.job_ids:
                                        if job.contact_id.active and ( job.contact_id.id not in sended_contacts ):
                                            if job.partner_sequence < current_sequence:
                                                current_job = job
                                                current_sequence = job.partner_sequence
                            record = []
                            if current_job:
                                record.append( ( current_job.contact_id.first_name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.title and current_job.contact_id.title.name or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.email or '' ).encode('cp1252') )
                                record.append( ( current_job.contact_id.mobile or '' ).encode('cp1252') )
                                record.append( ( current_job.phone or '' ).encode('cp1252') )
                                record.append( ( current_job.fax or '' ).encode('cp1252') )
                                record.append( ( current_job.email or '' ).encode('cp1252') )
                                record.append( ( current_job.function_label or '' ).encode('cp1252') )
                                record.append( ( current_job.function_label_code or '' ).encode('cp1252') )
                                if current_address.name and current_address.name[0] == '-':
                                    record.append( ( ' ' + current_address.name ).encode('cp1252') )
                                else:
                                    record.append( ( current_address.name or '' ).encode('cp1252') )
                                record.append( ( current_address.street or '' ).encode('cp1252') )
                                record.append( ( current_address.street2 or '' ).encode('cp1252') )
                                if current_address.zip_id.name == 'manuel':
                                    record.append( current_address.zip_id.city.encode('cp1252') )
                                else:
                                    record.append( ( current_address.zip_id.name + ' ' + current_address.zip_id.city ).encode('cp1252') )
                                record.append( ( current_address.email or '' ).encode('cp1252') )
                                record.append( partner.name.encode('cp1252') )
                                record.append( ( partner.title and partner.title.name or '' ).encode('cp1252') )
                                record.append( compose_fullname( partner.name, current_address.name ).encode('cp1252') )
                                record.append( current_job.contact_id.id )
                                record.append( current_job.id )
                                record.append( current_address.id )
                                record.append( partner.id )
                                record.append( 'newmember' )
                                record.append( (current_address.magazine_subscription or '' ).encode('cp1252') )
                                record.append( ( current_address.magazine_subscription_source or '' ).encode('cp1252') )
                                record.append( ( current_job.magazine_subscription or '' ).encode('cp1252') )
                                record.append( ( current_job.magazine_subscription_source or '' ).encode('cp1252') )
                                count_lines += 1
                                sended_contacts.append( current_job.contact_id.id )
                                sended_addresses.append( current_address.id )

                    foundPostal = False
                    for addr in partner.child_ids:
                        if ( addr.magazine_subscription in ['postal','personal'] and addr.zip_id and addr.active and not addr.notdelivered ) or ( addr.id in sended_addresses ):
                            foundPostal = True
                            break;
                        if dJobCont.has_key( addr.id ):
                            lJobCont = dJobCont[ addr.id ]
                            for jobCont in lJobCont:
                                if jobCont['magazine_subscription'] in ['postal','personal']:
                                    foundPostal = True
                                    break
                    if not foundPostal:
                        # we search for the first usable address
                        current_address = False
                        for addr in partner.child_ids:
                            if addr.type == 'default' and addr.zip_id and addr.active and not addr.notdelivered and addr.magazine_subscription != 'never':
                                current_address = addr
                                break
                        if not current_address:
                            for addr in partner.address:
                                if addr.type == 'invoice' and addr.zip_id and addr.active and not addr.notdelivered and addr.magazine_subscription != 'never':
                                    current_address = addr
                                    break
                        if not current_address:
                            current_sequence = 99999
                            for addr in partner.address:
                                if ( addr.type not in ['default','invoice'] ) and addr.zip_id and addr.active and not addr.notdelivered and addr.magazine_subscription != 'never':
                                    if addr.sequence_partner < current_sequence:
                                        current_address = addr
                                        current_sequence = addr.sequence_partner
                        if current_address:
                            current_job = False
                            if dJobCont.has_key( current_address.id ):
                                lJobCont = dJobCont[ current_address.id ]
                                for jobCont in lJobCont:
                                    if ( '1' in ( jobCont['function_code_label'] or '' ) ) and ( job['contact_id'] not in sended_contacts ):
                                        current_job = jobCont
                                if not current_job:
                                    for jobCont in lJobCont:
                                        if ( 'G' in ( jobCont['function_code_label'] or '' ) ) and ( job['contact_id'] not in sended_contacts ):
                                            current_job = jobCont
                                if not current_job:
                                    for jobCont in lJobCont:
                                        if jobCont['contact_id'] not in sended_contacts:
                                            current_job = jobCont
                            record = []
                            if current_job:
                                record.append( ( current_job['first_name'] or '' ).encode('cp1252') )
                                record.append( ( current_job['name'] or '' ).encode('cp1252') )
                                record.append( ( current_job['title'] or '' ).encode('cp1252') )
                                record.append( ( current_job['contact_email'] or '' ).encode('cp1252') )
                                record.append( ( current_job['mobile'] or '' ).encode('cp1252') )
                                record.append( ( current_job['phone'] or '' ).encode('cp1252') )
                                record.append( ( current_job['fax'] or '' ).encode('cp1252') )
                                record.append( ( current_job['job_email'] or '' ).encode('cp1252') )
                                record.append( ( current_job['function_label'] or '' ).encode('cp1252') )
                                record.append( ( current_job['function_code_label'] or '' ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                                record.append( '' )
                            record.append( ( current_address.type or '' ).encode('cp1252') )
                            if current_address.name and current_address.name[0] == '-':
                                record.append( ( ' ' + current_address.name ).encode('cp1252') )
                            else:
                                record.append( ( current_address.name or '' ).encode('cp1252') )
                            record.append( ( current_address.street or '' ).encode('cp1252') )
                            record.append( ( current_address.street2 or '' ).encode('cp1252') )
                            if current_address.zip_id.name == 'manuel':
                                record.append( current_address.zip_id.city.encode('cp1252') )
                            else:
                                record.append( ( current_address.zip_id.name + ' ' + current_address.zip_id.city ).encode('cp1252') )
                            record.append( ( current_address.email or '' ).encode('cp1252') )
                            record.append( partner.name.encode('cp1252') )
                            record.append( ( partner.title or '' ).encode('cp1252') )
                            record.append( compose_fullname( partner.name, current_address.name ).encode('cp1252') )
                            if current_job:
                                record.append( current_job['contact_id'] )
                                record.append( current_job['job_id'] )
                            else:
                                record.append( 0 )
                                record.append( 0 )
                            record.append( current_address.id )
                            record.append( partner.id )
                            record.append( 'newmember' )
                            record.append( ( current_address.magazine_subscription or '' ).encode('cp1252') )
                            record.append( ( current_address.magazine_subscription_source or '' ).encode('cp1252') )
                            if current_job:
                                record.append( ( current_job['magazine_subscription'] or '' ).encode('cp1252') )
                                record.append( ( current_job['magazine_subscription_source'] or '' ).encode('cp1252') )
                            else:
                                record.append( '' )
                                record.append( '' )
                            if partner.user_id:
                                record.append( partner.user_id.name.encode('cp1252') )
                            else:
                                record.append('')
                            hfCSV.writerow( record )
                            count_lines += 1
                            if current_job:
                                sended_contacts.append( current_job['contact_id'] )
                            sended_addresses.append( current_address.id )
            # step 4. Extract the possible prospects
            if self.prospect_limit > 0:
                # a limit is specified => we must collect new prospects to attain this limit in the file
                (count_lines,count_prospects) = collect_new_prospects(cr,uid,hfCSV,data['form']['prospect_limit'],count_lines,sended_contacts,sended_addresses)
            elif self.prospect_limit == 0:
                # no limit is given but the number isn't negative => we collect the same prospect as the past use
                (count_lines,count_prospects) = collect_same_prospects(cr,uid,hfCSV,count_lines,sended_contacts,sended_addresses)
            else:  ## negative number
                # no prospect, the file is finished
                count_prospects = 0
            
            msg = 'Save the File with '".csv"' extension.\nThe file has %s lines including %s prospects.' % (str(count_lines),str(count_prospects))
            ppi_file = base64.encodestring(ifile.getvalue())
            ctx['ppi'] = ppi_file
        except StandardError, err:
            msg = 'File NOT created.\n0 lines, 0 prospect...\n\nError :\n%s' % str(err)
        
        ctx['msg'] = msg
        
        
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.get.ppi.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

class wizard_get_ppi_msg(models.Model):

    _name = 'wizard.get.ppi.msg'
        
    name = fields.Char('File Name')
    msg = fields.Text('File Created', readonly=True)
    ppi = fields.Binary('Prepared File', readonly = True)
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_get_ppi_msg,self).default_get(fields)
        res[name] = 'ppi.csv'
        res['msg'] = self.env.context.get('mag','')
        res['ppi'] = self.env.context.get('ppi',False)
        return res
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

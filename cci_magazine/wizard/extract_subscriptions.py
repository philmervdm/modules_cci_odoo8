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

from openerp import models , fields , api , _ 

class extract_subscriptions(models.TransientModel):
    _name = 'extract.subscriptions'

    @api.multi
    def open_window_results(self):
        # delete all old values
        selection = "DELETE FROM cci_mag_subscription"
        self.env.cr.execute( selection )
        selection = '' # unusefull just for the case of
        # prepare the inserting of new data
        cci_mag_sub_obj = self.env['cci_mag_subscription']
        # get all addresses concerned
        selection = """SELECT res1.*, partner.id, partner.name, partner.membership_state
                       FROM
                           (SELECT addr.id, addr.parent_id as parent_id, addr.street, addr.street2, zip.name || ' ' || zip.city,  
                                   addr.magazine_subscription, addr.magazine_subscription_source 
                            FROM res_partner as addr, res_partner_zip as zip
                            WHERE addr.active AND addr.zip_id = zip.id and ( addr.magazine_subscription = 'postal' or addr.magazine_subscription = 'personal'
                                  or ( addr.magazine_subscription = 'prospect' and addr.magazine_subscription_source is not null )) ) as res1
                       LEFT OUTER JOIN (SELECT * from res_partner where active ) as partner ON ( res1.parent_id = partner.id )"""
        self.env.cr.execute( selection )
        addresses = self.env.cr.fetchall()
        
        for addr in addresses:
            # record the data
            record = { 'source':addr[6] or '',
                       'type':addr[5] or '',
                       'model':'adresse',
                       'partner_name':addr[8] or '',
                       'membership_state':addr[9] or '',
                       'street':addr[2] or '',
                       'street2':addr[3] or '',
                       'city':addr[4] or '',
                       'contact_name':'',
                       'first_name':'',
                       'partner_id':addr[1] or 0,
                       'address_id':addr[0],
                       'job_id':0,
                       'contact_id':0,
                     }
            new_id = cci_mag_sub_obj.create(record)
            
#         # get all jobs concerned
#         selection = """SELECT res1.*, partner.id, partner.name, partner.membership_state
#                        FROM
#                            (SELECT rpjob.id, contact.id, addr.id, addr.partner_id as partner_id, addr.street, addr.street2,
#                                    zip.name || ' ' || zip.city, rpjob.magazine_subscription, rpjob.magazine_subscription_source,
#                                    contact.name, contact.first_name 
#                             FROM res_partner_job as rpjob, res_partner_contact as contact, res_partner_address as addr, res_partner_zip as zip
#                             WHERE rpjob.active and rpjob.address_id = addr.id and rpjob.contact_id = contact.id and contact.active 
#                                   and addr.active AND addr.zip_id = zip.id and ( rpjob.magazine_subscription = 'postal' or rpjob.magazine_subscription = 'personal'
#                                   or ( rpjob.magazine_subscription = 'prospect' and rpjob.magazine_subscription_source is not null )) ) as res1
#                        LEFT OUTER JOIN (SELECT * from res_partner where active ) as partner ON ( res1.partner_id = partner.id )"""
#         cr.execute( selection )
#         jobs = cr.fetchall()
#         for job in jobs:
#             # record the data
#             record = { 'source':job[8] or '',
#                        'type':job[7] or '',
#                        'model':'fonction',
#                        'partner_name':job[12] or '',
#                        'membership_state':job[13] or '',
#                        'street':job[4] or '',
#                        'street2':job[5] or '',
#                        'city':job[6] or '',
#                        'contact_name':job[9],
#                        'first_name':job[10],
#                        'partner_id':job[3] or 0,
#                        'address_id':job[2],
#                        'job_id':job[0],
#                        'contact_id':job[1],
#                      }
#             new_id = cci_mag_sub_obj.create(cr, uid, record, context)
        
        result = {
            'name': _('CCI Mag Subscription'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'cci_mag_subscription',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


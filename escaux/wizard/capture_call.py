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
import datetime
import urllib
import StringIO
from lxml import etree
from osv import fields,osv
import wizard
import pooler
from tools.translate import _

class wizard_capture_call(wizard.interface):
    def _open_partner(self, cr, uid, data, context):
        pool_obj = pooler.get_pool(cr.dbname)
        model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_partner_form')])
        resource_id = pool_obj.get('ir.model.data').read(cr,uid,model_data_ids,fields=['res_id'])[0]['res_id']

        # extract the caller phone number from the list of active channels of Escaux Serveur
        # 1/ extract the Escaux server where the current user is connected to
        user = pool_obj.get('res.users').browse(cr, uid, uid, context=context)
        if not user.escaux_server_id.id:
            raise osv.except_osv(_('Error :'), _('No Escaux server configured for the current user.'))
        else:
            escaux_server = user.escaux_server_id

        # 2/ We check if the current user has an internal number
        if not user.sip_name:
            raise osv.except_osv(_('Error :'), _('No internal phone name configured for the current user'))

        # 3/ We extract the list of active channels from the Escaux SOP server
        res = urllib.urlopen( 'http://' + escaux_server.ip_address + '/xml/ccGetChannels.php' )
        stringXML = ''
        for line in res:
            stringXML += line
        root = etree.fromstring(stringXML)
        foundUser = False
        phone_nr = ''
        user_phone_name = 'SIP/' + user.sip_name
        for channel in list(root):
            lastCallerID = ''
            for element in list(channel):
                if element.tag == 'CallerId':
                    lastCallerID = element.text
                elif element.tag == "ID" and element.text[0:len(user_phone_name)] == user_phone_name:
                    foundUser = True
            if foundUser:
                phone_nr = lastCallerID[len(escaux_server.prefix_incoming):]
                break;

        # Check if the number to dial is not empty
        #print "extracted: *" + phone_nr + "*"
        if not phone_nr:
            raise osv.except_osv(_('Error :'), _('There is no phone number to retrieve for this user !'))
        # Note : if I write 'Error' without ' :', it won't get translated...
        # Alexis de Lattre doesn't understand why ! I agree ...

        # search for this phonenumber in the fields res.partner.job.phone then res.partner.contact.mobile and, if not yet found, res.partner.address.phone
        partner_id = 0
        job_ids = pool_obj.get('res.partner.job').search(cr,uid,[('phone','=',phone_nr)])
        foundRecord = False
        if job_ids:
            jobs = pool_obj.get('res.partner.job').browse(cr,uid,job_ids)
            for job in jobs:
                if job.address_id and job.address_id.partner_id:
                    # we found a job with an address linked to a partner, we can stop the search here
                    partner_id = job.address_id.partner_id.id
                    foundRecord = True
                    break
        if not foundRecord:
            # we don't found someone in jobs from the phonenumber so we try from contacts
            contact_ids = pool_obj.get('res.partner.contact').search(cr,uid,[('mobile','=',phone_nr)])
            if contact_ids:
                contacts = pool_obj.get('res.partner.contact').browse(cr,uid,contact_ids)
                print contacts
                for contact in contacts:
                    print contact
                    if contact.job_id and contact.job_id.address_id and contact.job_id.address_id.partner_id:
                        # we found a contact linked to a partner, we can stop the search here
                        partner_id = contact.job_id.address_id.partner_id.id
                        foundRecord = True
                        break
        if not foundRecord:
            # we don't found someone in jobs, nor in contacts, so we try in addresses
            address_ids = pool_obj.get('res.partner.address').search(cr,uid,[('phone','=',phone_nr)])
            if address_ids:
                addresses = pool_obj.get('res.partner.address').browse(cr,uid,address_ids)
                for address in addresses:
                    if address.partner_id:
                        # we found a address linked to a partner, we can stop the search here
                        partner_id = address.partner_id.id
                        foundRecord = True
                        break
        if not foundRecord:
            raise osv.except_osv(_('Error :'), _('This phone number is not found in our database !'))
            return {'type':'state','state':'end'}
        else:
            return {
                'domain': "[('id','=',"+str(partner_id)+")]",
                'name': 'Calling Partner',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'views': [(False,'tree'),(resource_id,'form')],
                'type': 'ir.actions.act_window'
            }
    states = {
        'init' : {
            'actions': [],
            'result': {'type':'action', 'action':_open_partner, 'state':'end'}
        }
    }
wizard_capture_call("escaux_wizard_capture_call")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Asterisk Click2dial module for OpenERP
#    Copyright (C) 2010 Alexis de Lattre <alexis@via.ecp.fr>
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
from openerp import models, fields , api , _ 
from openerp.exceptions import Warning
# Lib required to open a socket (needed to communicate with Asterisk server)
#import socket
import urllib
# Lib required to print logs
# Lib to translate error messages
# Lib for regexp
#import re
import logging

_logger = logging.getLogger(__name__)

class escaux_server(models.Model):
    '''Escaux server object, to store all the parameters of the ESCAUX SOP IPBXs'''
    _name = "escaux.server"
    _description = "Escaux Servers"

    name = fields.Char('Escaux server name', size=50, required=True, help="Escaux SOP comprehensive server name.")
    active = fields.Boolean('Active', default = True , help="The active field allows you to hide the Escaux server without deleting it.")
    ip_address = fields.Char('Escaux IP addr. or DNS', size=50, required=True, help="IPv4 address or DNS name of the Escaux server.")
    port = fields.Integer('Port', required=True, default=80, help="TCP port on which the Escaux SOP listens.")
    wait_time = fields.Integer('Wait time (sec)', default=15, required=True, help="Amount of time (in seconds) Escaux will try to reach the user's phone before hanging up.")
    company_id = fields.Many2one('res.company', 'Company', help="Company who uses the Escaux server.")
    prefix_incoming = fields.Char('Prefix incoming',size=10, help="number added to the usual number for the incoming call (often '0').")
    prefix_outcoming = fields.Char('Prefix outcoming',size=10, help="number added to the phone number recorded in database before going out (often '0').")

    @api.constrains('wait_time')
    def _check_wait_time(self):
        for i in self:
            wait_time_to_check = i.read(['wait_time'])['wait_time']
            if wait_time_to_check < 1 or wait_time_to_check > 120:
                raise Warning(_('You should enter a Wait time value between 1 and 120 seconds'))
        return True
    
    @api.constrains('port')
    def _check_port(self):
        for i in self:
            port_to_check = i.read(['port'])['port']
            if port_to_check > 65535 or port_to_check < 1:
                raise Warning(_('TCP ports range from 1 to 65535'))
        return True

    @api.multi
    def dial(self, erp_number):
        '''
        Send commands to Escaux Server to ring the phone with the external number given

        '''
#         logger = netsvc.Logger()
        user = self.env['res.users'].browse(self.env.uid)

        # Check if the number to dial is not empty
        if not erp_number:
            raise Warning(_('Error :'), _('There is no phone number to call !'))
        # Note : if I write 'Error' without ' :', it won't get translated...
        # Alexis de Lattre doesn't understand why ! I agree ...

        # We check if the user has an Escaux server configured
        if not user.escaux_server_id.id:
            raise Warning(_('Error :'), _('No Escaux server configured for the current user.'))
        else:
            escaux_server = user.escaux_server_id

        # We check if the current user has an internal number
        if not user.sip_name:
            raise Warning(_('Error :'), _('No internal phone name configured for the current user'))

        # The user should also have a CallerID
        #if not user.callerid:
        #    raise osv.except_osv(_('Error :'), _('No callerID configured for the current user'))

        # Convert the phone number in the format that will be sent to Escaux
        # in our case, the phone number are all encoded with the format '043419191' or '043419191 (private)'
        pos_final_parenthesis = erp_number.rfind( ' (' )
        if pos_final_parenthesis > -1:
            erp_number = erp_number[0:pos_final_parenthesis]
        
        _logger.debug('User dialing : channel = ' + user.sip_name)
        _logger.debug('Escaux server [' + escaux_server.name + '] = ' + escaux_server.ip_address + ':' + str(escaux_server.port))
        _logger.debug('Destination number:'+erp_number)
        
        # Connect to the Escaux Manager Interface, using IPv6-ready code
        try:
            if user.sip_extension:
                full_url = 'http://' + escaux_server.ip_address + '/xml/ccOriginate.php?' + urllib.urlencode([('phone_id',user.sip_name),('to',escaux_server.prefix_outcoming+erp_number),('ext',user.sip_extension)])
            else:
                full_url = 'http://' + escaux_server.ip_address + '/xml/ccOriginate.php?' + urllib.urlencode([('phone_id',user.sip_name),('to',escaux_server.prefix_outcoming+erp_number)])
            _logger.debug(full_url)
            req_res = urllib.urlopen(full_url)
        except:
            _logger.debug('Click2dial failed : unable to connect to Escaux')
            raise Warning(_('Error :'), _("The connection from OpenERP to the Escaux server failed. Please check the configuration on OpenERP and on Escaux."))

# Parameters specific for each user
class res_users(models.Model):
    _name = "res.users"
    _inherit = "res.users"
    sip_name = fields.Char('SIP Phone ID', size=15, help="User's phone name on Escaux SOP")
    escaux_server_id = fields.Many2one('escaux.server', 'Escaux server', help="Escaux server on which the user's phone is connected.")
    sip_extension = fields.Char('Phone extension',size=15,help='Show the attached phone number to external calls')

# this adds action click to dial to the phone field of res.partner.address
class res_partner_address(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    @api.multi
    def action_dial_phone(self):
        '''Function called by the button 'Dial' next to the 'phone' field
        in the partner address view'''
        erp_number = self.read(self.ids, ['phone'])[0]['phone']
        self.env['escaux.server'].dial(erp_number)

# # this adds action click to dial to the phone field of res.partner.job
# class res_partner_job(osv.osv):
#     _name = "res.partner.job"
#     _inherit = "res.partner.job"
# 
#     def action_dial_phone(self, cr, uid, ids, context=None):
#         '''Function called by the button 'Dial' next to the 'phone' field
#         in the partner job view'''
#         erp_number = self.read(cr, uid, ids, ['phone'], context=context)[0]['phone']
#         self.pool.get('escaux.server').dial(cr, uid, ids, erp_number, context=context)
# res_partner_job()
# 
# # this adds action click to dial to the mobile field of res.partner.contact
# class res_partner_contact(osv.osv):
#     _name = "res.partner.contact"
#     _inherit = "res.partner.contact"
# 
#     def action_dial_mobile(self, cr, uid, ids, context=None):
#         '''Function called by the button 'Dial' next to the 'mobile' field
#         in the partner contact view'''
#         erp_number = self.read(cr, uid, ids, ['mobile'], context=context)[0]['mobile']
#         self.pool.get('escaux.server').dial(cr, uid, ids, erp_number, context=context)
# res_partner_contact()

# This module supports multi-company

class res_company(models.Model):
    _name = "res.company"
    _inherit = "res.company"
    
    escaux_server_ids = fields.One2many('escaux.server', 'company_id', 'Escaux servers', help="List of Escaux servers.")

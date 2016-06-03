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
{
    'name' : 'CCI EVENT',
    'version' : '1.0',
    'author' : 'Tiny',
    'website' : 'http://www.openerp.com',
    'category' : 'Generic Modules/CCI',
    'description': '''
        specific module for cci project which will use Event module.
    ''',
    'depends' : [
        'event', 
        'account_payment', 
        'membership', 
        'cci_partner'
    ], #'cci_account', 
    'data' : [
        'security/security.xml',
        'security/ir.model.access.csv',
        'cci_event_view.xml',
        'cci_event_workflow.xml',
        'wizard/event_copy_view.xml',
        'wizard/cci_confirm_registrations_view.xml',
        'wizard/create_event_registration_view.xml',
        'wizard/create_partner_registration_view.xml',
        'wizard/registration_missing_checks_view.xml',
        'wizard/extract_registrations_view.xml',
    ],
    'demo' : [],
    'installable': True,
    'certificate': '00857068396250569805',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
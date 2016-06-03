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
    'name' : 'CCI EVENT EXTEND',
    'version' : '1.2',
    'author' : 'CCILVN - Philmer',
    'website' : 'http://www.ccilvn.be',
    'category' : 'Generic Modules/CCI',
    'description': '''
        specific module for cci project which will use Event module.
    ''',
    'depends' : ['cci_event', 'cci_premium'],
    'data' : [
        'cci_event_extend_view.xml',
        'wizard/extract_reg_with_activity_view.xml',
        'wizard/extract_registrations_for_carousel_view.xml',
        'wizard/extract_registrations_with_activity_view.xml',
        'wizard/extract_site_count_view.xml',
        'wizard/make_invoice_view.xml',
        'wizard/project_wizard_view.xml',
    ],
    'demo' : [],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
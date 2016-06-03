# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
{
    'name' : "CCI Member's Directory",
    'version' : '1.2',
    'author' : 'CCI Liege Verviers Namur',
    'website' : 'http://www.ccilvn.be',
    'category' : 'Generic Modules/CCI',
    'description': '''
        Add proxy tables to manage data for the update of records by CCI Members from a website
    ''',
    'depends' : ['base', 'cci_partner', 'cci_base_contact', 'cci_activity_sector' ], #'profile_cci', 
    'data' : [
        'security/security.xml',
        'security/ir.model.access.csv',
        'cci_memberdirectory_view.xml',
        'wizard/create_prospection_view.xml',
        'wizard/internal_validate_view.xml',
        'wizard/export_paper_view.xml',
        'wizard/manual_confirm_view.xml',
        'wizard/recup_internal_view.xml',
        'wizard/show_all_complex_view.xml',
        'wizard/show_all_simple_view.xml',
        'wizard/show_jobs_view.xml',
        'wizard/show_validated_simple_view.xml',
        'wizard/show_validated_complex_view.xml',
    ],
    'demo' : [],
    'active': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
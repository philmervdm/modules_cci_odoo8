# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (c) 2009 CCI  ASBL. (<http://www.ccilconnect.be>).
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
    'name': 'CCI Newsletter',
    'version': '1.0',
    'category': 'management',
    'description': """
        Module to help the CCI to manage their newsletter (Revue de Presse)
    """,
    'author': 'CCI Connect',
    'depends': [ 
        'base_contact',
#         'cci_last_module', 
#         'ftp_connection',
    ],
    'data': [ 
        'security/security.xml',
        'security/ir.model.access.csv',
        'cci_newsletter_view.xml',
        'wizard/extract_subscribers_view.xml',
        'wizard/import_wapi_file_view.xml',
        'wizard/send_site_update_view.xml',
    ],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

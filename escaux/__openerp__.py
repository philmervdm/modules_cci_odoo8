# -*- encoding: utf-8 -*-
##############################################################################
#
#    Escaux module for OpenERP
#    Copyright (C) 2011 Philmer - CCI Connect <philmer@cciconnect.be>
#    based on Asterisk Click2dial module for OpenERP
#             Copyright (C) 2010 Alexis de Lattre <alexis@via.ecp.fr>
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
    'name': 'Escaux',
    'version': '1.0',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'description': """
""",
    'author': 'philmer',
    'website': 'http://www.cciconnect.be/',
    'depends': ['base','base_contact'],
    'init': [],
    'data': ['escaux_server_view.xml', 
             'res_users_view.xml', 
#              'base_contact_view.xml',
#              'escaux_wizard.xml',
            'security/escaux_server_security.xml',
             ],
    'demo': [''],
    'installable': True,
    'active': False,
}


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
    'name': 'CCI YearBook',
    'version': '1.0',
    'category': 'data export',
    'description': """
        Module to export data in a dedicated format 
        for the creation of the yearbook of the magazine of
        the Belgian Chamber of Commerce and Industry : CCI Mag
    """,
    'author': 'CCI Connect',
    'depends': ['base','l10n_be_postal_subscriber'],
    'init': [],
    'data': [
                    'cci_yearbook_wizard.xml',
                   ],
    'demo': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

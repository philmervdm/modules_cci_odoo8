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
    'name': 'CCI Magazine',
    'version': '1.1',
    'category': 'management',
    'description': """
        Module that add some wizards and lists of controls to help
        the Chamber of Commerce to manage their magazine
    """,
    'author': 'CCI Connect',
    'depends': [ 'l10n_be_postal_subscriber', 
                 'base_contact',
                 'cci_premium',
               ],
    'init': [],
    'data': [
                    'cci_magazine_view.xml',
                    'cci_magazine_data.xml',
                    'security/security.xml',
                    'security/ir.model.access.csv',
                    'wizard/inactive_old_jobs.xml',
                    'wizard/extract_subscription.xml',
                    'wizard/get_ppi.xml',
                   ],
    'demo': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

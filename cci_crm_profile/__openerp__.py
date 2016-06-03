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
    "name" : "CCI CRM Profile",
    "version" : "1.0",
    "author" : "Odoo",
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/CCI",
    "description": """
        specific module for cci project which will use crm_profile module.
    """,
    "depends" : ["base","crm_profiling","base_contact"],
    "init" : [],
    "demo" : [],
    "data" : ["cci_crm_profile_view.xml",
              "wizard/open_questionnaire_view.xml",
              ],
    "active": False,
    "installable": True,
    'certificate': '001292404724499151029',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


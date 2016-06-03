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
    "name" : "CCI Sales",
    "version" : "1.1",
    "author" : "Tiny",
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/CCI",
    "description": """
        A Specific Module for CCI which will make the use of Sale module..
    """,
    "depends" : ["sale_advertising","crm"],
    "data" : ["cci_sales_view.xml",
              "cci_sales_wizard.xml"],
    "demo" : [],
    "auto_install": False,
    "installable": True,
    'certificate': '00693817273152452861',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


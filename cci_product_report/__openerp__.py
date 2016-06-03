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
    "name" : "CCI Product Report",
    "version" : "1.0",
    "author" : "CCILVN",
    "website" : "http://www.ccilvn.be",
    "category" : "Generic Modules/CCI",
    "description": """
        Specific module for add reports on product_product
    """,
    "depends" : ['product'],

    "data" : [
      'cci_product_report_report.xml',
      'report/control1_qweb.xml',
      'wizard/sales_purchase_view.xml',
      'wizard/sales_purchase_by_type_view.xml',
      #'cci_product_wizard.xml' Its  COMMNENTED BECAUSE THIS VIEW FILE NOT REQUIRED MORE, depracted with V8
      ],
    "demo" : [],
    "auto_install": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


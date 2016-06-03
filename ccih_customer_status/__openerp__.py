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
    "name" : "CCIH Customer Status",
    "version" : "1.0",
    "author" : "CCILVN",
    "website" : "http://www.ccilvn.be",
    "category" : "Generic Modules/CCI",
    "description": """
        specific module for the CCIH to output the customer status
    """,
    "depends" : ["base_vat","cci_partner","account_payment"],
    "demo" : [],
    "data" : [
        'ccih_customer_status_wizard.xml',
        'report/ccih_customer_status_report.xml',
        'report/customer_status_report_qweb.xml',
        ],
    "auto_install": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


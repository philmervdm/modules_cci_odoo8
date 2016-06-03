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
    "name" : "CCI Membership",
    "version" : "1.0",
    "author" : "Tiny",
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/CCI",
    "description": """
        cci membership
            - vcs functionality for cci
    """,
    "depends" : ["base","membership","cci_event"],
    "init" : [],
    "demo" : [],
    "data" : ['cci_membership_view.xml',
              'cci_membership_report.xml',
              'security/security.xml',
              'security/ir.model.access.csv', 
              'cci_membership_data.xml',
              'wizard/member_total_sold.xml',
              'wizard/show_partners.xml',
              'wizard/cci_invoice_membership.xml',
              'wizard/cci_check_membership.xml',
              'wizard/select_invoices_by_year.xml',
              'report/report_total_sold.xml'
              ],
              
    "active": False,
    "installable": True,
    'certificate': '00571378930833485069',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


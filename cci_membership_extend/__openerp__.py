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
    "name" : "CCI Membership Extend",
    "version" : "1.3",
    "author" : "CCI Connect",
    "website" : "http://www.cci.connect.be",
    "category" : "Generic Modules/CCI",
    "description": """
        cci membership extend
            - extend the membership
    """,
    "depends" : ["membership","cci_membership"],
    "init" : [],
    "demo" : [],
    "data" : ["cci_membership_extend_view.xml",'security/security.xml',
                'security/ir.model.access.csv',
                'wizard/extract_sponsor_partners.xml',
                 'wizard/extract_nonstandard_amounts.xml',
                 'wizard/extract_used_membership_amount.xml',
                 'wizard/extract_asked_less_billed.xml',
                 'wizard/extract_prospect_addsite.xml',
                 'wizard/extract_partners_by_amount.xml',
                 'wizard/extract_calls_in_excel.xml',
                 'wizard/extract_special_calls_in_excel.xml',
                 'wizard/extract_membership_by_partner.xml',
                 'wizard/membership_calls.xml',
                 'wizard/membership_calls_2_excel.xml',
                 'wizard/membership_partners_to_invoice.xml',
                 'wizard/cci_invoice_membership.xml',
                 'wizard/new_members_since.xml',
                 'wizard/detect_old_but_not_yet_billed.xml',
                 'wizard/use_membership_products.xml',
                 'wizard/membership_followup.xml',
                 'wizard/extract_membership_by_year.xml',
                 'wizard/compare_paid2years.xml',
                 'wizard/compare_paid_multiple_years.xml',
#                 "cci_membership_extend_wizard.xml"
                ],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


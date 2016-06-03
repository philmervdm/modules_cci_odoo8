# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    "name" : "Analytic Account Report Extension 1",
    "version" : "1.2",
    "author" : "CCI Connect",
    "category": '',
    "description": """Analytic Account Report with two or three analytic plans crossed with account move lines
                        and others reports specific to CCI""",
    'website': 'http://www.cciconnect.be',
    "depends" : ['account','cci_report'],
    'data': [
        'wizard/crossed_analytic_report_view.xml',
        'security/ir.model.access.csv',
        'cci_report_extend_report.xml',
        'views/report_partner_commercial.xml',
        'views/report_partner_internal.xml',
    ],

    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

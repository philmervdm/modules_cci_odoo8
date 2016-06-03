# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Belgian 281.50 data',
    'version': '1.0',
    'category': 'Generic Modules/Accounting',
    'description': """Accounting Extractions of belgian 281.50 data for the CCI
                      The 281.50 data serve to communicate to suppliers not subjected
                      to VAT the amount of purchases done by them,
                      as the belgian VAT need this information for the annual tax declaration    
    """,
    'author': 'CCILVN',
    'website': 'http://www.ccilvn.be',
    'depends': ['account','l10n_be'],
    'init': [],
    'data': [
        'cci_account_281_50_view.xml',
        'cci_account_281_50_report.xml',
        'security/ir.model.access.csv',
        'wizard/extract281_50.xml',
        'wizard/prepare281_50.xml',
        'report/report_sheet_281_50.xml'
    ],
    'demo': [],
    'installable': True,
    'active': False,
}


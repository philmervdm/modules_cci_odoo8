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
    "name" : "CCI Purchase",
    "version" : "1.0",
    "author" : "Tiny",
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/CCI",
    "description": """
        specific module for cci project which will use purchase module
    """,
    "depends" : ["base","purchase"],

    "data" : [
                "cci_purchase_view.xml",
                "cci_purchase_workflow.xml",
                "security/ir.model.access.csv"
            ],
    "active": False,
    "installable": True,
    'certificate': '00476149109026953629',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


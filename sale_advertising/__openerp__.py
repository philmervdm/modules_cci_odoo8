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
# 1.1 2011-11-16 Philmer added the related fields user_id on sale.order.line
{
    "name" : "Sales: Avertising Sales",
    "version" : "1.1",
    "author" : "Odoo",
    "category" : "Generic Modules/Sales & Purchases",
    "website" : "http://www.openerp.com",
    "description": """This module allow you to use the Sale Management to encode your advertising sales ... TODO
""",
    "depends" : ["sale","stock_account"],
    "init" : [],
    "demo" : ["sale_advertising_demo.xml"],
    "data" : ["security/ir.model.access.csv","sale_advertising_view.xml",],
    "active": False,
    "installable": True,
    'certificate': '00897881177027633069',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


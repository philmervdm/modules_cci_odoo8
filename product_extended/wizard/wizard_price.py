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

import wizard
import pooler

def _compute_price(self, cr, uid, data, context):
    bom_obj = pooler.get_pool(cr.dbname).get('mrp.bom')
    #product_obj = pooler.get_pool(cr.dbname).get('product.product')

    for bom in bom_obj.browse(cr, uid, data['ids'], context=context):
        bom.product_id.compute_price(cr, uid, bom.product_id.id)
    return {}


class wizard_price(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _compute_price,
                    'state' : 'end'}
        },
    }
wizard_price('product_extended.compute_price')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


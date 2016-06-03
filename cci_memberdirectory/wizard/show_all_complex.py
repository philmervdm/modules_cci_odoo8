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

from openerp import models, fields, api, _

class cci_show_all_complex(models.TransientModel):
    _name = 'cci.show.all.complex'
    
    @api.multi
    def show_all_complex(self):
        obj_addr = self.env['directory.address.proxy']
        obj_complex = self.env['directory.complex']
        complex_ids = obj_complex.search([])
        complexs = complex_ids.read(['partner_id'])
        lComplexs = [x['partner_id'][0] for x in complexs]
        addr_ids = obj_addr.search([])
        addresses = addr_ids.read(['id', 'partner_id', 'full_page'])
        final_ids = []
        for addr in addresses:
            if addr['partner_id'][0] in lComplexs or addr['full_page']:
                final_ids.append(addr['id'])
        value = {
            'domain': [('id', 'in', final_ids)],
            'name': 'Complex Address Proxy',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'directory.address.proxy',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
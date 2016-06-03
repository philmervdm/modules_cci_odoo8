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

from openerp import models, fields, api , _


class wizard_view_companies(models.TransientModel):
    _name = 'view.companies'
    
    @api.multi
    def show_companies(self):
        premium_contact_id = self.env.context.get('active_id') #data['id']
        value = {
            'domain': [('premium_contact_id', '=', premium_contact_id)],
            'name': 'Premium Form Company',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'premium_company',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return value
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


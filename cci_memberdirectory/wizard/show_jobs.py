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

class show_jobs_addr_proxy(models.TransientModel):
    _name = 'show.jobs.addr.proxy'
    
    @api.multi
    def show_jobs(self):
        address_proxy_id = self.env.context.get('active_id', False)
        #obj_todo = pooler.get_pool(cr.dbname).get('crm_cci.todo')
        #current_todo = obj_todo.read(cr,uid,data['id'],['partner'])
        #print current_todo
        value = {
            'domain': [('address_proxy_id', '=', address_proxy_id)],
            'name': 'Jobs Proxy',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'directory.job.proxy',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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
# This wizard replace the same wizardfrom event_project to adapt it to our needs

import time
from openerp import models, fields, api, _

class cci_event_extend_project(models.TransientModel):
    _name = 'cci.event.extend.project'
    
    project_id = fields.Many2one('project.project', string='Project Template', required=True, domain=[('active', '<>', False), ('state', '=', 'template')])
    
    @api.multi 
    def create_duplicate(self):
        event_obj = self.env['event.event']
        event = event_obj.browse(self.env.context['active_id'])
        event_data = event.read(['name'])
        project_obj = self.env['project.project']
        duplicate_project_id = self.project_id.copy({'active': True})
        duplicate_project_id.write({'name': event_data[0]['name'] , 'date_start':time.strftime('%Y-%m-%d'), 'date': event_obj.browse(self.env.context['active_id']).date_begin[0:10]})
        event.write({'project_id': duplicate_project_id.id})
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
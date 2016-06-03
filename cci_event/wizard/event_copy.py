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

from openerp import models, fields, api, _

class event_copy(models.TransientModel):
    _name = 'event.copy'
    
    nbr_event = fields.Char('Event Copied', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(event_copy, self).default_get(fields)
        if self.env.context.has_key('active_ids'):
            res.update({'nbr_event': str(len(self.env.context['active_ids']))})
        return res
    
    @api.multi    
    def makecopy(self):
        obj_event = self.env['event.event']
        count = 0
        for event in obj_event.browse(self.env.context['active_ids']):
            count = count + 1
            event.copy()
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
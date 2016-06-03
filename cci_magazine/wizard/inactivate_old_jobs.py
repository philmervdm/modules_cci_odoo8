# -*- coding: utf-8 -*-
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

from openerp import models, fields , api , _ 

class inactivate_old_jobs(models.TransientModel):
    _name = 'inactive.old.jobs'
    
    @api.multi
    def launch_method(self):
        obj_job = self.env['res.partner']
        ids_list = obj_job._inactivate_old()
        msg = 'Inactivated %s jobs with a past "End Job Date".\nList of id : %s' % (str(len(ids_list)),'[' + ','.join([str(x) for x in ids_list]) + ']')
        ctx = self.env.context.copy()
        ctx.update({'msg':msg})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'inactive.old.jobs.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
        
class inactivate_old_msg(models.TransientModel):
    _name = 'inactive.old.jobs.msg'
    
    msg = fields.Text(string = 'The test has been done', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(inactivate_old_msg, self).default_get(fields)
        res.update({'msg': self.env.context.get('msg','')})
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

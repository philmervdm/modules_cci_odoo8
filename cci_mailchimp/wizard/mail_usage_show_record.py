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
# Version 1.0 Philmer
# This wizard searchs for emails addresses in a list of given table

import time
import datetime
from openerp import models, fields, api, _

class cci_mailchimp_show_record(models.TransientModel):
    _name = 'cci.mailchimp.show.record'
    
    @api.multi
    def show(self):
        obj_usage = self.env['mail_usage']
        usage = obj_usage.browse(self.env.context['active_id'])
        mail_usage = usage.read(['source', 'source_id'])
        source_ids = [mail_usage['source_id'][0]]
        value = {
            'domain': [('id', 'in', source_ids)],
            'name': _('Associated Record'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': mail_usage['source'],
            'context': {},
            'type': 'ir.actions.act_window',
        }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
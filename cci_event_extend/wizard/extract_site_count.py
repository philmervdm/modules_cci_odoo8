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
# this script extract counting of inscriptions done by a certain user (the web site) for events between two dates

import time
import datetime
import base64
from xlwt import *

from openerp import tools
from openerp import models, fields, api, _

class extract_site_count(models.TransientModel):
    _name = 'extract.site.count'
    
    from_count = fields.Date(string='From', required=True)
    to = fields.Date(string='To',  required=True)
    user_id = fields.Many2one('res.users', string='Site User', required=True)
    
    @api.multi
    def get_file(self):
        obj_event = self.env['event.event']
        obj_registration = self.env['event.registration']

        wb1 = Workbook()
        ws1 = wb1.add_sheet('Count of Site Registrations by Event')
        ws1.write(0, 0, 'event_id')
        ws1.write(0, 1, 'event_name')
        ws1.write(0, 2, 'count_site')
        ws1.write(0, 3, 'count_total')
        line = 1

        # extract all events between the two given dates
        events = obj_event.search([('date_begin', '>=', self.from_count), ('date_begin', '<=', self.to)])
        if events:
#             events = obj_event.browse(event_ids)
            sentence = """SELECT count(event_id), event_id
                            FROM event_registration as reg, crm_case as crm 
                            WHERE reg.event_id in (%s) 
                                AND (crm.state = 'open' OR crm.state = 'done')
                                AND reg.create_uid = %s
                                AND reg.case_id = crm.id
                            GROUP BY event_id""" % (','.join([str(x.id) for x in events]),
                                                                str(data['form']['user_id']))
            self.env.cr.execute(sentence)
            count_site = {}
            count_total = {}
            for event_id in events:
                count_site[event_id.id] = 0
                count_total[event_id.id] = 0
            res = self.env.cr.fetchall()
            for count in res:
                count_site[count[1]] = count[0]
            sentence = """SELECT count(event_id), event_id
                            FROM event_registration as reg, crm_case as crm 
                            WHERE reg.event_id in (%s) 
                                AND (crm.state = 'open' OR crm.state = 'done')
                                AND reg.case_id = crm.id
                            GROUP BY event_id""" % (','.join([str(x) for x in events.ids]))
            self.env.cr.execute(sentence)
            res = self.env.cr.fetchall()
            for count in res:
                count_total[count[1]] = count[0]
            for event in events:
                ws1.write(line, 0, event.id)
                ws1.write(line, 1, event.name or 'inconnu')
                ws1.write(line, 2, count_site[event.id])
                ws1.write(line, 3, count_total[event.id])
                line += 1
            wb1.save('site_counting.xls')
            result_file = open('site_counting.xls', 'rb').read()

            # give the result to the user
            msg = 'Save the File with '".xls"' extension.'
            site_counting_xls = base64.encodestring(result_file)
        else:
            wb1.save('site_counting.xls')
            result_file = open('site_counting.xls', 'rb').read()
            msg = 'No events between these two dates.'
            site_counting_xls = base64.encodestring(result_file)
            
        ctx = self.env.context.copy()
        ctx.update({'msg': msg, 'site_counting_xls': site_counting_xls, 'name': 'site_counting.xls'})
        
        resource = self.env.ref('cci_event_extend.cci_extract_site_count_msg_view')
        return {
            'name': 'Notification',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'extract.site.count.msg',
            'views': [(resource.id, 'form')],
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class extract_site_count_msg(models.TransientModel):
    _name = 'extract.site.count.msg'
    
    name = fields.Char('Name')
    msg = fields.Text('File created', size=100, readonly=True)
    site_counting_xls = fields.Binary('Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(extract_site_count_msg, self).default_get(fields)
        if 'name' in self.env.context:
            res.update({'name': self.env.context['name']})
        if 'msg' in self.env.context:
            res.update({'msg': self.env.context['msg']})
        if 'site_counting_xls' in self.env.context:
            res.update({'site_counting_xls': self.env.context['site_counting_xls']})
        return res
     

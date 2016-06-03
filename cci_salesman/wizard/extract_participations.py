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
import datetime

def _club_active_participations(self, cr, uid, data, context):
    club_id = data['id']
#    cr.execute('SELECT p.id FROM cci_club_participation as p, cci_club_participation_state as s WHERE p.group_id = %s AND ( p.date_out is null OR p.date_out > %s ) #AND p.state_id = s.id AND s.current', (club_id, datetime.date.today() ))
#    res = cr.fetchall()
#    part_ids = [x[0] for x in res]
#    value = {
#        'domain': [('id', 'in', part_ids)],
#        'name': 'Active Participations',
#        'view_type': 'form',
#        'view_mode': 'tree,form',
#        'res_model': 'cci_club.participation',
#        'context': {},
#        'type': 'ir.actions.act_window'
#    }
# THE FOLLOWING WAY IS MORE DYNAMIC
    value = {
        'domain': [('group_id', '=', club_id),('state_id.current','=',True),'|',('date_out','=',False),('date_out','>',datetime.date.today().strftime('%Y-%m-%d') )],
        'name': 'Active Participations',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'cci_club.participation',
        'context': {},
        'type': 'ir.actions.act_window'
    }
    return value

class wizard_club_active_participations(wizard.interface):
    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'action',
                'action': _club_active_participations,
                'state': 'end'
            }
        },
    }
wizard_club_active_participations("wizard_cci_club_active_participations")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


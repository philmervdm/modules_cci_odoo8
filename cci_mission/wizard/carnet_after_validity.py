# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

from openerp import models, fields , api , _

class ata_carnet_after_validity(models.TransientModel):
    _name = 'ata.carnet.after.validity'
    
    @api.multi
    def print_report(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type' : 'ir.actions.report.xml',
            'report_name':'cci_mission.carnet_after_validity',
            'datas' : datas
       }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
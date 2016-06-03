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
import time
from datetime import datetime as dt
from openerp.report import report_sxw
from openerp import models, api

class carnet_after_validity(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(carnet_after_validity, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'carnet_after': self._carnet_after,
        })

    def _carnet_after(self):
        res = {}
        res_list = []
        after_date = dt.now() + dt.RelativeDateTime(months=+1)
        after_date  = after_date.strftime("%Y-%m-%d")
        carnet_obj = self.pool.get('cci_missions.ata_carnet')
        carnet_ids = carnet_obj.search(self.cr, self.uid, [('validity_date', '>=', after_date), ('state', '>=', 'created')])
        carnet_data = carnet_obj.browse(self.cr, self.uid, carnet_ids)
        for carnet in carnet_data:
            flag = False
            address = ''
            for letter in carnet.letter_ids:
                if letter.letter_type == 'Rappel apres echeance':
                    flag = True
            if not flag:
                if carnet.partner_id.child_ids:
                    for add in carnet.partner_id.child_ids:
                        if add.type=='default':
                            address = (add.street or '') + ' ' + (add.street2 or '') + '\n' + (add.zip_id and add.zip_id.name or '') + ' ' + (add.city or '')  + '\n' + (add.state_id and add.state_id.name or '') + ' ' + (add.country_id and add.country_id.name or '')
                            continue
                        else:
                            address = (add.street or '') + ' ' + (add.street2 or '') + '\n' + (add.zip_id and add.zip_id.name or '') + ' ' + (add.city or '')  + '\n' + (add.state_id and add.state_id.name or '') + ' ' + (add.country_id and add.country_id.name or '')
                res = { 'partner_name': carnet.partner_id.name,
                        'partner_address': address,
                        'type': carnet.type_id.name,
                        'name': carnet.name,
                        'creation_date': carnet.creation_date,
                        'validity_date': carnet.validity_date
                      }

                res_letter = {
                      'letter_type': 'Rappel apres echeance',
                      'date': time.strftime('%Y-%m-%d'),
                      'ata_carnet_id': carnet.id,
                              }
                self.pool.get('cci_missions.letters_log').create(self.cr, self.uid, res_letter)
                res_list.append(res)
        return res_list

class carnet_after_val(models.AbstractModel):
    _name = 'report.cci_mission.carnet_after_validity'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.carnet_after_validity'
    _wrapped_report_class = carnet_after_validity

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


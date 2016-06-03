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
from openerp import models, fields ,api , _
import time

class report_carnet_print1(models.TransientModel):
    _name = 'report.carnet.print'
    
    header = fields.Integer(string = 'Header No. of pages', default=1) # field1
    export = fields.Integer(string = 'Export No. of pages', default=4) # field2
    importpg = fields.Integer(string = 'Import No. of pages', default=4) # field3
    transit = fields.Integer(string = 'Transit No. of pages', default=20) #field4
    reexport = fields.Integer(string = 'Re-Exportation No. of pages', default=4) # field5
    reimport = fields.Integer(string = 'Re-Importation No. of pages', default=4) # field6
    presence = fields.Integer(string = 'Presence No. of pages', default=1) # field7
    export_reimport = fields.Integer(string = 'Voucher export/re-importation No. of pages', default=1) # field8
    import_reexport = fields.Integer(string = 'Voucher import/re-exportation No. of pages', default=1) # field9
    vtransit = fields.Integer(string = 'Vtransit No. of pages', default=5) # field10
    
    @api.multi
    def print_carnet_report1(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_header', data=datas, context=self.env.context)

    @api.multi
    def print_carnet_report2(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_export', data=datas, context=self.env.context)

    @api.multi
    def print_carnet_report3(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_import', data=datas, context=self.env.context)
        
    @api.multi
    def print_carnet_report4(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_transit', data=datas, context=self.env.context)

    @api.multi
    def print_carnet_report5(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_reexport', data=datas, context=self.env.context)
    
    @api.multi
    def print_carnet_report6(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_reimport', data=datas, context=self.env.context)
    
    @api.multi
    def print_carnet_report7(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_presence', data=datas, context=self.env.context)
        

    @api.multi
    def print_carnet_report8(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_export_reimport', data=datas, context=self.env.context)
    
    @api.multi
    def print_carnet_report9(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_import_reexport', data=datas, context=self.env.context)

    @api.multi
    def print_carnet_report10(self):
        datas = {'ids' : self.env.context.get('active_ids',[])}
        res = self.read([])
        res = res and res[0] or {}
        res.update(datas)
        datas['form'] = res
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [], 'cci_mission.report_print_carnet_vtransit', data=datas, context=self.env.context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

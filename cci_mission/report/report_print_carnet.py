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
import time
from openerp.report import report_sxw
from openerp import models, api

class print_carnet_header(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_header, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['header']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_hea(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_header'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_header'
    _wrapped_report_class = print_carnet_header


class print_carnet_export(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_export, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['export']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagenum':str(i),
                    'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_exp(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_export'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_export'
    _wrapped_report_class = print_carnet_export


class print_carnet_import(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_import, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['importpg']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagenum':str(i),
                    'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_impo(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_import'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_import'
    _wrapped_report_class = print_carnet_import


class print_carnet_transit(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_transit, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['transit']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            if (i%2)==0:
                pagenum = str((i+1)//2)+'B'
            else:
                pagenum = str((i+1)//2)+'A'
            page = {'pagenum':pagenum,
                    'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_trans(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_transit'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_transit'
    _wrapped_report_class = print_carnet_transit


class print_carnet_reexport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_reexport, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['reexport']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagenum':str(i),
                    'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_reexpo(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_reexport'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_reexport'
    _wrapped_report_class = print_carnet_reexport


class print_carnet_reimport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_reimport, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['reimport']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagenum':str(i),
                    'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_reimpo(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_reimport'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_reimport'
    _wrapped_report_class = print_carnet_reimport


class print_carnet_presence(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_presence, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['presence']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'cciname':carnet_obj.type_id.site_id.official_name_1,
                    'carnetname':carnet_obj.name,
                    'material':carnet_obj.usage_id.name,
                    'vyear':carnet_obj.validity_date[0:4],
                    'vmonth':carnet_obj.validity_date[5:7],
                    'vday':carnet_obj.validity_date[8:],
                    'holdername':carnet_obj.holder_name,
                    'holderaddr':carnet_obj.holder_address,
                    'holderzipcity':carnet_obj.holder_city,
                    'reprname':carnet_obj.representer_name,
                   }
            pages.append(page)
        return pages

class print_carnet_pres(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_presence'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_presence'
    _wrapped_report_class = print_carnet_presence


class print_carnet_export_reimport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_export_reimport, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['export_reimport']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagea':str((i*4)-3),
                    'pageb':str((i*4)-2),
                    'carnetname':carnet_obj.name,
                   }
            pages.append(page)
            page = {'pagea':str((i*4)-1),
                    'pageb':str(i*4),
                    'carnetname':carnet_obj.name,
                   }
            pages.append(page)
        return pages

class print_carnet_exp_reimpo(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_export_reimport'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_export_reimport'
    _wrapped_report_class = print_carnet_export_reimport

class print_carnet_import_reexport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_import_reexport, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['import_reexport']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagea':str((i*4)-3),
                    'pageb':str((i*4)-2),
                    'carnetname':carnet_obj.name,
                   }
            pages.append(page)
            page = {'pagea':str((i*4)-1),
                    'pageb':str(i*4),
                    'carnetname':carnet_obj.name,
                   }
            pages.append(page)
        return pages

class print_carnet_exp_reiexpo(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_import_reexport'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_import_reexport'
    _wrapped_report_class = print_carnet_import_reexport


class print_carnet_vtransit(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_carnet_vtransit, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,'get_pages':self._get_pages})
    def _get_pages(self, form):
        nbre_pages = form['vtransit']
        objects = self.pool.get('cci_missions.ata_carnet').browse(self.cr,self.uid,form['ids'][0])
        carnet_obj = objects[0]
        pages = []
        for i in range(1,nbre_pages+1):
            page = {'pagea':str((i*4)-3)+'A',
                    'pageb':str((i*4)-3)+'B',
                    'pagec':str((i*4)-2)+'A',
                    'paged':str((i*4)-2)+'B',
                    'carnetname':carnet_obj.name,
                   }
            pages.append(page)
            page = {'pagea':str((i*4)-1)+'A',
                    'pageb':str((i*4)-1)+'B',
                    'pagec':str(i*4)+'A',
                    'paged':str(i*4)+'B',
                    'carnetname':carnet_obj.name,
                   }
            pages.append(page)
        return pages

class print_carnet_exp_reiexpo(models.AbstractModel):
    _name = 'report.cci_mission.report_print_carnet_vtransit'
    _inherit = 'report.abstract_report'
    _template = 'cci_mission.report_print_carnet_vtransit'
    _wrapped_report_class = print_carnet_vtransit

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


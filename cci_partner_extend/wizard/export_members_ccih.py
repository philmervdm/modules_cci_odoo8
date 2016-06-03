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
from openerp import models, fields, api, _
import datetime
import base64
from xlwt import *

class wizard_export_members_ccih(models.TransientModel):
    _name = 'wizard.export.members.ccih'
    category_id = fields.Many2one('res.partner.category', string='Activity Sector Parent Category')

    @api.model
    def create_data(self, data):
        res = {}
        def get_phone_country_prefix():
            result = []
            obj_country = self.env['cci.country']
            country_ids = obj_country.search([('phoneprefix','!=',False),('phoneprefix','!=',0)])
            if country_ids:
                countries = country_ids.read(['phoneprefix'])
                result = [str(x['phoneprefix']) for x in countries]
            return result
        def convert_phone(string,PHONE_COUNTRY_PREFIX):
            def only_digits(string):
                cleaned = ''
                for carac in string:
                    if carac in '0123456789':
                        cleaned += carac
                return cleaned
            result = ''
            string = only_digits(string)
            if len(string) > 0:
                if len(string) == 9:
                    if string[0:2] in ['02','03','04','09']:
                        result = string[0:2] + "/" + string[2:5] + "." + string[5:7] + "." + string[7:]
                    else:
                        result = string[0:3] + "/" + string[3:5] + "." + string[5:7] + "." + string[7:]
                elif len(string) == 10:
                    result = string[0:4] + "/" + string[4:6] + "." + string[6:8] + "." + string[8:]
                else:
                    # international number
                    #print string
                    if string[0:2] == '00':
                        # search after a country with this prefix
                        prefix = string[2:4]
                        if prefix not in PHONE_COUNTRY_PREFIX:
                            prefix = string[2:5]
                            if prefix not in PHONE_COUNTRY_PREFIX:
                                prefix = string[2:6]
                                if prefix not in PHONE_COUNTRY_PREFIX:
                                    prefix = ''
                        if prefix:
                            result = '+' + string[2:2+len(prefix)] + ' ' + string[2+len(prefix):4+len(prefix)]
                            rest = string[4+len(prefix):]
                            while len(rest) > 3:
                                result += '.' + rest[0:2]
                                rest = rest[2:]
                            result += '.' + rest
                        else:
                            result = 'International:'+string
            return result
        category_id = self.category_id
        if category_id:
            # extract all ids of activity sector categories and remove '[303]' from name
            obj_categ = self.env['res.partner.category']
            old_len = 0
            categ_ids = [ category_id ]
            while len(categ_ids) > old_len:
                new_ids = categ_ids[old_len:] # ids of categories added last time
                old_len = len(categ_ids) # the new frontier ...
                new_categs = new_ids.read(['child_ids'])
                for categ in new_categs:
                    if categ['child_ids']:
                        categ_ids.extend(categ['child_ids'])
            categs = categ_ids.read(['name'])
            dCategs = {}
            for categ in categs:
                formated_name = categ['name']
                posA = formated_name.rfind('[')
                posB = formated_name.rfind(']')
                if posA > 0 and posB > 0 and posA < posB:
                    formated_name = formated_name[0:posA-1]
                dCategs[ categ['id'] ] = formated_name
    
        # extract all active members
        obj_partner = self.env['res.partner']
        partner_ids = obj_partner.search([('state_id','=',1),('membership_state','in',['paid','free','invoiced'])])
        partners = partner_ids.browse()
        wb = Workbook()
        ws = wb.add_sheet('liste')
        ws.write(0,0,u'Entreprise')
        ws.write(0,1,u'Adresse')
        ws.write(0,2,u'Adresse2')
        ws.write(0,3,u'CP')
        ws.write(0,4,u'Localité')
        ws.write(0,5,u'Tél')
        ws.write(0,6,u'Fax')
        ws.write(0,7,u'Email général')
        ws.write(0,8,u'Site Web')
        ws.write(0,9,u'Fonction')
        ws.write(0,10,u'Nom')
        ws.write(0,11,u'Prénom')
        ws.write(0,12,u'Civilité')
        ws.write(0,13,u'Effectif')
        ws.write(0,14,u'TVA')
        if category_id:
            ws.write(0,15,u'Secteur')
        line = 1
        PREFIXES = get_phone_country_prefix()
        for partner in partners:
            for address in partner.child_ids:
                if address.type == 'default' or address.local_employee:
                    ws.write(line,0,partner.name)
                    ws.write(line,1,address.street or '' )
                    ws.write(line,2,address.street2 or '' )
                    ws.write(line,3,address.zip or '' )
                    ws.write(line,4,address.city or '' )
                    ws.write(line,5,convert_phone(address.phone or '',PREFIXES) )
                    ws.write(line,6,convert_phone(address.fax or '',PREFIXES) )
                    ws.write(line,7,address.email or '' )
                    ws.write(line,8,partner.website or '' )
                    min_seq = 999
                    id_min_seq = False
                    id_seq0 = False
                    for job in address.other_contact_ids:
                        if job.sequence_partner < min_seq and job.sequence_partner > 0:
                            min_seq = job.sequence_partner
                            id_min_seq = job.id
                        if not id_seq0 and job.sequence_partner == 0:
                            id_seq0 = job.id
                    if id_min_seq or id_seq0:
                        selected_job_id = id_seq0
                        if id_min_seq:
                            selected_job_id = id_min_seq
                        for job in address.other_contact_ids:
                            if job.id == selected_job_id:
                                ws.write(line,9,job.function_label or '' )
                                if job.contact_id:
                                    ws.write(line,10,job.contact_id.name)
                                    ws.write(line,11,job.contact_id.first_name or '' )
                                    ws.write(line,12,job.contact_id.title.name or '' )
                    ws.write(line,13,max(0,partner.employee_nbr or 0) or 'nc')
                    ws.write(line,14,partner.vat or '' )
                    if category_id:
                        for categ in partner.category_id: ## category_id is, not like his name define, an array of category ids
                            if categ.id in categ_ids:
                                ws.write(line,15,dCategs[categ.id])
                                break
                    line += 1
        wb.save('membres_ccih.xls')
        result_file = open('membres_ccih.xls','rb').read()
        # give the result to the user
        msg ='Save the File with '".xls"' extension.'
        res.update({'msg': msg})
        res.update({'membres_ccih': base64.encodestring(result_file)})
        result = {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.export.members.ccih2',
            'target': 'new',
            'context': {'res':res, 'name': 'membres_ccih.xls'},
            'type': 'ir.actions.act_window'
        }
        return result

class wizard_export_members_ccih2(models.TransientModel):
    _name = 'wizard.export.members.ccih2'
   
    msg = fields.Text(string ='File Created', readonly=True)
    membres_ccih = fields.Binary(string= 'Prepared file', readonly=True)
    name = fields. Char(string ='File Name')

    @api.model
    def default_get(self,fields):
        res = super(wizard_export_members_ccih2, self).default_get(fields)
        context = dict(self._context or {})
        res.update({
            'msg': context['res']['msg'],
            'membres_ccih': context['res']['membres_ccih'],
            'name': 'membres_ccih.xls'
        })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

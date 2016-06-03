# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 CCI Connect ASBL. (http://www.cciconnect.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import datetime
from openerp import models, fields, api, _

def _only_digits(string):
    result = [x for x in string if x.isdigit()]
    return ''.join(result)

def _correct_escape(string):
    return string.replace("\\" + "'", "'").replace("\\" + '"', '"')

def _check_digit_1_digit(digital_string):
    digit_sum = 0
    for carac in digital_string:
        if carac.isdigit():
            digit_sum += int(carac)
    return str(digit_sum)[-1:]

def _convert_phone(string, PHONE_COUNTRY_PREFIX):
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
            if string[0:2] in ['02', '03', '04', '09']:
                result = string[0:2] + "/" + string[2:5] + "." + string[5:7] + "." + string[7:]
            else:
                result = string[0:3] + "/" + string[3:5] + "." + string[5:7] + "." + string[7:]
        elif len(string) == 10:
            result = string[0:4] + "/" + string[4:6] + "." + string[6:8] + "." + string[8:]
        else:
            # international number
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
                    result = '+' + string[2:2 + len(prefix)] + ' ' + string[2 + len(prefix):4 + len(prefix)]
                    rest = string[4 + len(prefix):]
                    while len(rest) > 3:
                        result += '.' + rest[0:2]
                        rest = rest[2:]
                    result += '.' + rest
                else:
                    result = 'International:' + string
    return result

def _convert_vat(vat):
    if vat and vat[0:2] == 'BE':
        result = vat[0:2] + '-' + vat[2:6] + '.' + vat[6:9] + '.' + vat[9:]
    else:
        result = vat
    return result

def split_address(string):
    if string.count(',') == 1:
        (street, number_and_box) = string.split(',')
        street = street.strip()
        number_and_box = number_and_box.strip()
        if ' BTE ' in number_and_box:
            (number, box) = number_and_box.split(' BTE ')
            number = number.strip()
            box = box.strip()
        else:
            number = number_and_box
            box = ''
    else:
        street = string.strip()
        number = ''
        box = ''
    return (street, number, box)

def get_activity_sectors(partner, oldcateg_ids, dOldSectID2NewID):
    secteurs = [False, False, False]
    current_secteur = 0
    if partner.category_id:
        for oldcateg in partner.category_id:  # # category_id is, not like his name define, an array of category ids
            if (oldcateg.id in oldcateg_ids) and (oldcateg.id not in secteurs) and dOldSectID2NewID.has_key(oldcateg.id):
                secteurs[current_secteur] = dOldSectID2NewID[oldcateg.id]
                current_secteur += 1
                if current_secteur > 2:
                    break
    return secteurs

class directory_address_proxy(models.Model):
    _name = 'directory.address.proxy'
    _description = "proxy partner and address 4 yearly members'directory"
    
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    address_id = fields.Many2one('res.partner', 'Address', required=True)
    link_id = fields.Char('Link ID', size=13, required=True)
    complete_name = fields.Char('Complete Name', size=200)
    partner_name = fields.Char('Partner Name', size=200)
    address_name = fields.Char('Address Name', size=200)
    dir_show_name = fields.Char('Dir Show Name', size=200)
    dir_sort_name = fields.Char('Dir Sort Name', size=200)
    street = fields.Char('Street', size=200)
    street_number = fields.Char('Street Number', size=20)
    street_box = fields.Char('Street Box', size=20)
    zip_code = fields.Char('Zip Code', size=15)
    city = fields.Char('City', size=50)
    phone = fields.Char('Phone', size=40)
    fax = fields.Char('Fax', size=40)
    email = fields.Char('eMail', size=200)
    web = fields.Char('Web', size=200)
    vat_num = fields.Char('VAT', size=40)
    employee = fields.Integer('Employee')
    desc_activ = fields.Text('Activity')
    origin_activ = fields.Char('Origin Activ', size=10)  # 'defpartner' : from partner on default address; 'partner' = from partner on other address; 'address' : from address record
    comments = fields.Text('User Comments')
    sector1 = fields.Char('Sector1', size=6)
    sector2 = fields.Char('Sector2', size=6)
    sector3 = fields.Char('Sector3', size=6)
    new_complete_name = fields.Char('Complete Name', size=200)
    new_street = fields.Char('Street', size=200)
    new_street_number = fields.Char('New Street Number', size=20)
    new_street_box = fields.Char('New Street Box', size=20)
    new_zip_code = fields.Char('Zip Code', size=4)
    new_city = fields.Char('City', size=50)
    new_phone = fields.Char('Phone', size=40)
    new_fax = fields.Char('Fax', size=40)
    new_email = fields.Char('eMail', size=200)
    new_web = fields.Char('Web', size=200)
    new_vat_num = fields.Char('VAT', size=40)
    new_employee = fields.Integer('Employee')
    new_desc_activ = fields.Text('Activity')
    new_sector1 = fields.Char('Sector1', size=6)
    new_sector2 = fields.Char('Sector2', size=6)
    new_sector3 = fields.Char('Sector3', size=6)
    final_partner_name = fields.Char('Partner Name', size=200)
    final_address_name = fields.Char('Address Name', size=200)
    final_dir_show_name = fields.Char('Dir Show Name', size=200)
    final_dir_sort_name = fields.Char('Dir Sort Name', size=200)
    final_street = fields.Char('Street', size=200)
    final_street_number = fields.Char('Final Street Number', size=20)
    final_street_box = fields.Char('Final Street Box', size=20)
    final_zip_id = fields.Many2one('res.partner.zip', 'Zip Code')
    final_phone = fields.Char('Phone', size=40)
    final_fax = fields.Char('Fax', size=40)
    final_email = fields.Char('eMail', size=200)
    final_web = fields.Char('Web', size=200)
    final_vat_num = fields.Char('VAT', size=40)
    final_employee = fields.Integer('Employee')
    final_sector1 = fields.Many2one('res.partner.activsector', 'Sector1',)
    final_sector2 = fields.Many2one('res.partner.activsector', 'Sector2',)
    final_sector3 = fields.Many2one('res.partner.activsector', 'Sector3',)
    final_desc_activ = fields.Text('Final Desc Activ')
    final_addr_desc_activ = fields.Text('Final Addr Desc Activ')
    not_in_directory = fields.Boolean('Not in directory')
    final_not_in_directory = fields.Boolean('Final Not in directory')
    user_validated = fields.Boolean('Validated by User')
    internal_validated = fields.Boolean('Validated by CCI')
    sending_address = fields.Char('Sending Address', size=200)
    sending_name = fields.Char('Sending Name', size=60)
    sending_courtesy = fields.Char('Sending Courtesy', size=60)
    send_initial_mail = fields.Datetime('Send Initial Mail')
    send_first_followup = fields.Datetime('Send Followup Mail')
    job_ids = fields.One2many('directory.job.proxy', 'address_proxy_id', 'Jobs')
    # 'deleted_job_ids = fields.One2many('directory.job2delete','address_proxy_id','Jobs marked for deletion')
    change_date = fields.Datetime('Change Date')
    full_page = fields.Boolean('Full Page for this edition')
    full_page_app = fields.Boolean('Full Page on App Directory')
    active = fields.Boolean('Active', default=True)
    write_date = fields.Datetime('Last Modification')
    write_uid = fields.Many2one('res.users', 'Last Modifier', help='The last person who has modified this contact')
    
    @api.multi
    def name_get(self):
        if not len(self.ids):
            return []
        reads = self.read(['complete_name'])
        res = []
        for record in reads:
            name = record['complete_name']
            res.append((record['id'], name))
        return res
     
    @api.multi
    def write(self, vals):
        result = False
        for current in self:
            if vals.has_key('user_validated') and vals['user_validated'] == False and len(vals) == 1:
                result = super(directory_address_proxy, self).write(vals)
            else:
                if vals.has_key('new_complete_name'):
                    vals.update({'final_partner_name':'', 'final_address_name':'', 'final_dir_show_name':'', 'final_dir_sort_name':'', 'internal_validated':False})
                if vals.has_key('new_web'):
                    vals.update({'final_web':(vals['new_web'] or '').replace('http://', ''), 'internal_validated':False})
                if vals.has_key('new_vat_num'):
                    new_vat_num = (vals['new_vat_num'] or '').replace('/', '').replace('-', '').replace('.', '').replace(' ', '')
                    if len(new_vat_num) == 9:
                        new_vat_num = 'BE0' + new_vat_num
                    elif len(new_vat_num) == 10:
                        new_vat_num = 'BE' + new_vat_num
                    elif len(new_vat_num) == 11 and new_vat_num[2:3] != '0':
                        new_vat_num = 'BE0' + new_vat_num[3:]
                    vals.update({'final_vat_num':new_vat_num, 'internal_validated':False})
                if vals.has_key('new_street'):
                    vals.update({'final_street':vals['new_street'], 'internal_validated':False})
                if vals.has_key('new_street_number'):
                    vals.update({'final_street_number':vals['new_street_number'], 'internal_validated':False})
                if vals.has_key('new_street_box'):
                    vals.update({'final_street_box':vals['new_street_box'], 'internal_validated':False})
                if vals.has_key('new_zip_code') or vals.has_key('new_city'):
                    zip_obj = self.pool.get('res.partner.zip')
                    new_zip_code = vals.get('new_zip_code', current.zip_code) or ''
                    new_city = vals.get('new_city', current.city) or ''
                    zip_ids = zip_obj.search([('name', '=', new_zip_code), ('city', 'ilike', new_city)])
                    if not zip_ids:
                        # search in other names
                        zip_ids = zip_obj.search([('name', '=', new_zip_code), ('other_names', 'ilike', new_city)], limti=1)
                    if zip_ids:
                        vals.update({'final_zip_id': zip_ids.id, 'internal_validated': False})
                    else:
                        found = False
                        zips = zip_ids.read(['name', 'city'])
                        for zip_record in zips:
                            if len(zip_record['city']) == len(new_city):
                                vals.update({'final_zip_id':zip_record['id'], 'internal_validated':False})
                                found = True
                                break
                        if not found:
                            vals.update({'final_zip_id':False, 'internal_validated':False})
                if vals.has_key('new_sector1') or vals.has_key('new_sector2') or vals.has_key('new_sector3'):
                    sector_obj = self.env['res.partner.activsector']
                if vals.has_key('new_sector1'):
                    if not vals['new_sector1']:
                        vals.update({'final_sector1':False, 'internal_validated':False})
                    else:
                        sector_ids = sector_obj.search([('code', '=', vals['new_sector1'])], limit=1)
                        if sector_ids:
                            vals.update({'final_sector1':sector_ids.id, 'internal_validated':False})
                if vals.has_key('new_sector2'):
                    if not vals['new_sector2']:
                        vals.update({'final_sector2':False, 'internal_validated':False})
                    else:
                        sector_ids = sector_obj.search([('code', '=', vals['new_sector2'])], limit=1)
                        if sector_ids:
                            vals.update({'final_sector2':sector_ids.id, 'internal_validated':False})
                if vals.has_key('new_sector3'):
                    if not vals['new_sector3']:
                        vals.update({'final_sector3':False, 'internal_validated':False})
                    else:
                        sector_ids = sector_obj.search([('code', '=', vals['new_sector3'])], limit=1)
                        if sector_ids:
                            vals.update({'final_sector3': sector_ids.id, 'internal_validated': False})
                if vals.has_key('new_phone'):
                    new_phone = _only_digits(vals['new_phone'] or '')
                    vals.update({'final_phone':new_phone, 'internal_validated':False})
                if vals.has_key('new_fax'):
                    new_fax = _only_digits(vals['new_fax'] or '')
                    vals.update({'final_fax':new_fax, 'internal_validated':False})
                if vals.has_key('new_employee') and vals['new_employee'] != 0:
                    vals.update({'final_employee':vals['new_employee'], 'internal_validated':False})
                if vals.has_key('new_desc_activ'):
                    if current.origin_activ in ('defpartner', 'partner'):
                        vals.update({'final_desc_activ':vals['new_desc_activ'], 'internal_validated':False})
                    else:
                        vals.update({'final_addr_desc_activ':vals['new_desc_activ'], 'internal_validated':False})
                if vals.has_key('new_email'):
                    vals.update({'final_email':vals['new_email'], 'internal_validated':False})
                if vals.has_key('not_in_directory'):
                    vals.update({'final_not_in_directory':vals['new_not_in_directory'], 'internal_validated':False})
                result = super(directory_address_proxy  , self).write(vals)
        return result
     
    @api.multi
    def but_confirm_changes(self):
        for current in self:
            if current.internal_validated:
                raise Warning(_('Error !'), _('This record has already been updated.'))
            else:
                new_partner_data = {}
                new_address_data = {}
                if current.final_partner_name:
                    new_partner_data['name'] = _correct_escape(current.final_partner_name)
                if current.final_web:
                    new_partner_data['website'] = _correct_escape(current.final_web)
                if current.final_employee:
                    new_partner_data['employee_nbr'] = current.final_employee  # # CORRECT BOTH TO KEEP THEM SYNCHRO
                    new_partner_data['employee_nbr_total'] = current.final_employee
                if current.final_vat_num and current.final_vat_num != 'BE0000000000':
                    new_partner_data['vat'] = current.final_vat_num
                if current.final_desc_activ and current.origin_activ == 'defpartner':
                    new_partner_data['activity_description'] = _correct_escape(current.final_desc_activ)
                if current.final_address_name:
                    new_address_data['name'] = (current.final_address_name == '/') and '' or  _correct_escape(current.final_address_name)
                if current.final_dir_show_name:
                    new_address_data['dir_show_name'] = (current.final_dir_show_name == '/') and '' or  _correct_escape(current.final_dir_show_name)
                if current.final_dir_sort_name:
                    new_address_data['dir_sort_name'] = (current.final_dir_sort_name == '/') and '' or  _correct_escape(current.final_dir_sort_name)
                if current.final_street or current.final_street_number or current.final_street_box:
                    new_address_data['street'] = _correct_escape(current.final_street or '')
                    if current.final_street_number:
                        new_address_data['street'] += ', ' + _correct_escape(current.final_street_number)
                    if current.final_street_box:
                        new_address_data['street'] += ' BTE ' + _correct_escape(current.final_street_box)
                if current.final_zip_id:
                    new_address_data['zip_id'] = current.final_zip_id.id
                if current.final_phone:
                    new_address_data['phone'] = (current.final_phone == '/') and '' or current.final_phone  # # TODO nettoyage formatage
                if current.final_fax:
                    new_address_data['fax'] = (current.final_fax == '/') and '' or current.final_fax  # # TODO nettoyage formatage
                new_address_data['sector1'] = current.final_sector1 and current.final_sector1.id or False
                new_address_data['sector2'] = current.final_sector1 and current.final_sector2.id or False
                new_address_data['sector3'] = current.final_sector1 and current.final_sector3.id or False
                if current.final_email:
                    new_address_data['email'] = (current.final_email == '/') and '' or current.final_email
                if current.final_addr_desc_activ:
                    new_address_data['activity_description'] = _correct_escape((current.final_addr_desc_activ == '/') and '' or current.final_addr_desc_activ)
                if current.final_not_in_directory:
                    new_address_data['dir_exclude'] = current.final_not_in_directory
                new_partner_data['date_lastcheck'] = datetime.datetime.today().strftime('%Y-%m-%d')
                current.partner_id.with_context({'lang':'fr_FR'}).write(new_partner_data)
                current.address_id.with_context({'lang':'fr_FR'}).write(new_address_data)
                # Update of contacts linked to the proxy record
                job_obj = self.pool.get('res.partner')
                contact_obj = self.pool.get('res.partner')
                # address_obj = self.pool.get('res.partner.address')
                # partner_obj = self.pool.get('res.partner.partner')
                jobs_in_sequence = []
                proxy_jobs_treated = []
                for job_proxy in current.job_ids:
                    proxy_jobs_treated.append(job_proxy.id)
                    if job_proxy.marked_for_deletion:
                        if job_proxy.job_id and job_proxy.contact_id:
                            if job_proxy.contact_id.job_ids and len(job_proxy.contact_id.job_ids) == 1 and job_proxy.contact_id.job_ids[0].contact_id.id == job_proxy.job_id.id:
                                job_proxy.contact_id.write({'active': False})
                            job_proxy.job_id.write({'active': False})
                    else:
                        if job_proxy.job_id:  # # and job_proxy.final_last_name == job_proxy.job_id.contact_id.name:
                            # print 'put changes in db'
                            jobs_in_sequence.append(job_proxy.job_id.id)
                            # we put the changes in db
                            def_mobile = False
                            if job_proxy.final_mobile and job_proxy.final_mobile != '0400000000':
                                def_mobile = job_proxy.final_mobile
                                if job_proxy.final_mobile_confidential:
                                    def_mobile += ' (conf)'
                            job_proxy.contact_id.write({'name': _correct_escape(job_proxy.final_last_name),
                                                        'first_name':  _correct_escape(job_proxy.final_first_name),
                                                        'title':  _correct_escape(job_proxy.final_courtesy),
                                                        'gender': job_proxy.final_gender,
                                                        'mobile': def_mobile,  # # TODO nettoyage formatage
                                                    })
                            job_proxy.job_id.write({'sequence_directory':job_proxy.final_sequence or job_proxy.new_sequence or job_proxy.sequence,
                                                                        'function_label':  _correct_escape(job_proxy.final_title),
                                                                        'email': job_proxy.final_email,
                                                                        'function_code_label': job_proxy.final_categs,
                                                                       })
                        else:
                            if job_proxy.new_last_name:
                                # we have to create a new contact and link him to this company
                                # or search for an existing contact in the same address
                                existing_job_id = 0
                                existing_contact_id = 0
                                if current.address_id:
                                    for job in current.address_id.other_contact_ids:
                                        inserted_last_name = (job_proxy.new_last_name or '').strip()
                                        inserted_first_name = (job_proxy.final_first_name or '').strip()
                                        if job.contact_id and job.contact_id.name.strip() == inserted_last_name and (job.contact_id.first_name or '').strip() == inserted_first_name:
                                            existing_job_id = job.id
                                            existing_contact_id = job.contact_id.id
                                            break
                                if existing_job_id == 0 or existing_contact_id == 0:
                                    # print 'create new contact and job'
                                    def_mobile = False
                                    if job_proxy.new_mobile and job_proxy.new_mobile != '0400000000':
                                        def_mobile = job_proxy.new_mobile
                                        if job_proxy.new_mobile_confidential:
                                            def_mobile += ' (conf)'
                                    new_contact_id = contact_obj.create({'name': _correct_escape(job_proxy.new_last_name),
                                                                        'first_name': _correct_escape(job_proxy.new_first_name or ''),
                                                                        'title': job_proxy.final_courtesy,
                                                                        'gender': job_proxy.final_gender,
                                                                        'mobile': def_mobile or False,  # # TODO nettoyage
                                                               })
                                    new_job_id = job_obj.create({'sequence_directory':job_proxy.final_sequence or job_proxy.new_sequence or job_proxy.sequence,
                                                                        'sequence_partner':99,
                                                                        'sequence_contact':1,
                                                                        'sequence_yearbook':job_proxy.new_sequence or job_proxy.sequence,
                                                                        'function_label':  _correct_escape(job_proxy.new_title),
                                                                        'email': job_proxy.new_email,
                                                                        'function_code_label': job_proxy.final_categs,
                                                                        'contact_id':new_contact_id,
                                                                        'address_id':current.address_id.id,
                                                                        'partner_id':current.partner_id.id,
                                                                       })
                                else:
                                    # print 'change data for found job'
                                    changes = {}
                                    if job_proxy.final_courtesy:
                                        changes['title'] = _correct_escape(job_proxy.final_courtesy)
                                    if job_proxy.final_gender:
                                        changes['gender'] = job_proxy.final_gender
                                    def_mobile = False
                                    if job_proxy.new_mobile and job_proxy.new_mobile != '0400000000':
                                        def_mobile = job_proxy.new_mobile
                                        if job_proxy.new_mobile_confidential:
                                            def_mobile += ' (conf)'
                                    changes['mobile'] = def_mobile
                                    if changes:
                                        existing_contact_id.write(changes)
                                    changes = {}
                                    changes['sequence_directory'] = job_proxy.final_sequence or job_proxy.new_sequence or job_proxy.sequence
                                    if job_proxy.final_title:
                                        changes['function_label'] = _correct_escape(job_proxy.final_title)
                                    if job_proxy.final_email:
                                        changes['email'] = job_proxy.final_email
                                    if job_proxy.final_categs:
                                        changes['function_code_label'] = job_proxy.final_categs
                                    job_obj.browse(existing_job_id).write(changes)
                                    new_job_id = existing_job_id
                                # jobs_in_sequence.append(new_job_id)
                if proxy_jobs_treated:
                    self.env['directory.job.proxy'].write(proxy_jobs_treated, {'internal_validated':True})
                # self.write(cr, uid, ids, {'internal_validated':True})
                # self.write(cr, uid, ids, {'user_validated':False}) # we put the record once again modifiable
                # we keep this record but as 'inactive' to keep track of the user's work
                # so to refresh the record and put it again modifiable thru website, we create new record for this address
                self.write({'internal_validated':True, 'active':False})  # we put the record once again modifiable
                self._synchro_address(current.address_id, current.partner_id, [current.id, ], current.full_page_app and [current.id, ] or [], False, False, False, False, False, False)
        return True
     
    @api.model
    def get_phone_country_prefix(self):
        result = []
        obj_country = self.env['cci.country']
        country_ids = obj_country.search([('phoneprefix', '!=', False), ('phoneprefix', '!=', 0)])
        if country_ids:
            countries = country_ids.read(['phoneprefix'])
            result = [str(x['phoneprefix']) for x in countries]
        return result
     
    @api.model
    def _get_sector_dicts(self):
        obj_categ = self.env['res.partner.activsector']
        categ_ids = obj_categ.search([])
        categs = categ_ids.read(['code'])
        dCategs = {}
        dSectCode2ID = {}
        for categ in categs:
            dCategs[categ['id']] = categ['code']
            dSectCode2ID[categ['code']] = categ['id']
        # table for converting old activity sectors to new ones
        dOldSectID2NewID = {}
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['ActivityCodeRootID'])
        if param_values.has_key('ActivityCodeRootID'):
            activityCodeRootID = param_values['ActivityCodeRootID']
            obj_oldcateg = self.pool.get('res.partner.category')
            old_len = 0
            oldcateg_ids = [ activityCodeRootID ]
            while len(oldcateg_ids) > old_len:
                new_ids = oldcateg_ids[old_len:]  # ids of categories added last time
                old_len = len(oldcateg_ids)  # the new frontier ...
                new_categs = new_ids.read(['child_ids'])
                for categ in new_categs:
                    if categ['child_ids']:
                        oldcateg_ids.extend(categ['child_ids'])
            oldcategs = oldcateg_ids.with_context({'lang':'fr_FR'}).read(['name'])
            for oldcateg in oldcategs:
                formated_name = oldcateg['name']
                posA = formated_name.rfind('[')
                posB = formated_name.rfind(']')
                if posA >= 0 and posB > 0 and posA < posB:
                    code = formated_name[posA + 1:posB]
                    if dSectCode2ID.has_key(code):
                        dOldSectID2NewID[oldcateg['id']] = dSectCode2ID[code]
        return (dCategs, dSectCode2ID, dOldSectID2NewID, oldcateg_ids)
     
    @api.model
    def _synchro_address(self, addr, partner, modifiable_proxy_ids, full_page_partner_ids, always_create, user_website_id, dCategs, dSectCode2ID, dOldSectID2NewID, oldcateg_ids):
        # addr = browse object, partner = browse object or false (then extracted from addr)
        # dCategs = dictionnaire des nouveaux secteurs d'activités, mais peut-être à 'False'
        partner_no_email = ''
        addr_count = 0
        modif_count = 0
        email_count = 0
        cont_count = 0
        if not partner:
            partner = addr.partner_id
        if not dCategs:
            (dCategs, dSectCode2ID, dOldSectID2NewID, oldcateg_ids) = self._get_sector_dicts()
        if not user_website_id:
            user_website_id = self.env['res.users'].search([('name', '=', 'Noomia')], limit=1)
        if addr.type <> 'invoice' and partner:
            addr_proxy_obj = self.env['directory.    .proxy']
            cont_proxy_obj = self.env['directory.job.proxy']
            link_id = _link_id(addr.id)
            PHONE_COUNTRY_PREFIX = self.get_phone_country_prefix()
            sector_ids = []
            if addr.sector1:
                sector_ids.append(addr.sector1.id)
                if addr.sector2:
                    sector_ids.append(addr.sector2.id)
                    if addr.sector3:
                        sector_ids.append(addr.sector3.id)
            else:
                (sector1, sector2, sector3) = get_activity_sectors(partner, oldcateg_ids, dOldSectID2NewID)
                sector_ids = [sector1, sector2, sector3]
            addr_data = {'link_id':link_id, 'partner_id':partner.id, 'address_id':addr.id}
            if addr.dir_show_name:
                addr_data['complete_name'] = addr.dir_show_name
            else:
                if addr.name:
                    if addr.name[0:2] == '- ' or addr.name[0:3] == ' - ':
                        addr_data['complete_name'] = partner.name.strip() + ' ' + addr.name.strip()
                    else:
                        addr_data['complete_name'] = addr.name.strip()
                else:
                    addr_data['complete_name'] = partner.name.strip()
            addr_data['partner_name'] = partner.name.strip()
            addr_data['address_name'] = (addr.name or '').strip()
            addr_data['dir_show_name'] = (addr.dir_show_name or '').strip()
            addr_data['dir_sort_name'] = (addr.dir_sort_name or '').strip()
            (addr_data['street'], addr_data['street_number'], addr_data['street_box']) = split_address(addr.street or '')
            addr_data['zip_code'] = (addr.zip_id and addr.zip_id.name or '')
            addr_data['city'] = (addr.zip_id and addr.zip_id.city or '')
            addr_data['phone'] = _convert_phone(addr.phone or '', PHONE_COUNTRY_PREFIX)
            addr_data['fax'] = _convert_phone(addr.fax or '', PHONE_COUNTRY_PREFIX)
            addr_data['email'] = (addr.email or '')
            addr_data['web'] = (partner.website or '')
            addr_data['vat_num'] = _convert_vat(partner.vat or '')
            addr_data['employee'] = (partner.employee_nbr_total or 0)
            if addr.activity_description:
                addr_data['desc_activ'] = addr.activity_description
                addr_data['origin_activ'] = 'address'
            else:
                addr_data['desc_activ'] = partner.activity_description or ''
                addr_data['origin_activ'] = (addr.type == 'default') and 'defpartner' or 'partner'
            addr_data['final_partner_name'] = partner.name.strip()
            addr_data['final_address_name'] = (addr.name or '').strip()
            addr_data['final_dir_show_name'] = (addr.dir_show_name or '').strip()
            addr_data['final_dir_sort_name'] = (addr.dir_sort_name or '').strip()
            (addr_data['final_street'], addr_data['final_street_number'], addr_data['final_street_box']) = split_address(addr.street or '')
            addr_data['final_zip_id'] = (addr.zip_id and addr.zip_id.id or False)
            addr_data['final_phone'] = addr.phone or ''
            addr_data['final_fax'] = addr.fax or ''
            addr_data['final_email'] = (addr.email or '')
            addr_data['final_web'] = (partner.website or '')
            addr_data['final_vat_num'] = partner.vat or ''
            addr_data['final_employee'] = (partner.employee_nbr_total or 0)
            addr_data['final_desc_activ'] = ''
            addr_data['final_dir_show_name'] = addr.dir_show_name or ''
            addr_data['final_dir_sort_name'] = addr.dir_sort_name or ''
            addr_data['sector1'] = False
            addr_data['sector2'] = False
            addr_data['sector3'] = False
            addr_data['final_sector1'] = False
            addr_data['final_sector2'] = False
            addr_data['final_sector3'] = False
            addr_data['full_page_app'] = (partner.id in full_page_partner_ids)
            if sector_ids and sector_ids[0]:
                addr_data['sector1'] = dCategs[sector_ids[0]]
                addr_data['final_sector1'] = sector_ids[0]
                if len(sector_ids) > 1 and sector_ids[1]:
                    addr_data['sector2'] = dCategs[sector_ids[1]]
                    addr_data['final_sector2'] = sector_ids[1]
                    if len(sector_ids) > 2 and sector_ids[2]:
                        addr_data['sector3'] = dCategs[sector_ids[2]]
                        addr_data['final_sector3'] = sector_ids[2]
            # either we create a new record proxy for address, either we change the old one, either, we do noting
            address_method = 'create'
            addr_proxy_id = False
            if not always_create:
                existing_ids = addr_proxy_obj.search([('address_id', '=', addr_data['address_id'])])
                if len(existing_ids) == 1:
                    existing = existing_ids.read(['partner_name', 'address_name', 'dir_show_name', 'dir_sort_name', 'street', 'zip_code', 'city', 'full_page_app',
                                                                        'phone', 'fax', 'email', 'web', 'vat_num', 'employee', 'desc_activ', 'origin_activ', 'sector1', 'sector2', 'sector3',
                                                                        'link_id', 'user_validated', 'internal_validated', 'write_uid'])[0]
                    the_same = True
                    if not existing['user_validated'] and not existing['internal_validated'] and existing['write_uid'] != user_website_id:
                        for field_name in ['partner_name', 'address_name', 'dir_show_name', 'dir_sort_name', 'street', 'zip_code', 'city', 'full_page_app', 'phone', 'fax', 'email', 'web', 'vat_num', 'employee', 'desc_activ', 'origin_activ', 'link_id']:
                            if existing[field_name] != addr_data[field_name]:
                                the_same = False
                    if not the_same:
                        address_method = 'write'
                        addr_proxy_id = existing_ids[0]
                    else:
                        address_method = 'nothing'
            if address_method == 'create':
                addr_proxy_id = addr_proxy_obj.create(addr_data)
                modifiable_proxy_ids.append(addr_proxy_id)
                addr_count += 1
            elif address_method == 'write' and addr_proxy_id and addr_proxy_id in modifiable_proxy_ids:
                addr_proxy_id.write(addr_data)
                modif_count += 1
            # extraction of contacts
            # we extract two kinds of contacts : the contacts to be published and the contact allowed to modify the record
            if addr_proxy_id and addr_proxy_id in modifiable_proxy_ids:
                selected_jobs = []
                sending_address = ''
                sending_name = ''
                sending_courtesy = ''
                sending_sequence = 9999
                if addr.job_ids:
                    for job in addr.job_ids:
                        if job.contact_id:
                            new_job = {
                               'sequence':job.sequence_directory or 99,
                               'last_name':job.contact_id.name,
                               'first_name':job.contact_id.first_name or '',
                               'address_proxy_id':addr_proxy_id,
                               'job_id':job.id,
                               'contact_id':job.contact_id.id,
                               'address_id':addr.id,
                               'email': job.email or job.contact_id.email or '',
                               'mobile': _convert_phone(job.contact_id.mobile or '', PHONE_COUNTRY_PREFIX),
                               'mobile_confidential':'conf' in (job.contact_id.mobile or ''),
                               'title': job.function_label or '',
                               'categs': job.function_code_label or '',
                               'final_last_name':job.contact_id.name,
                               'final_first_name':job.contact_id.first_name or '',
                               'final_email': job.email or job.contact_id.email or '',
                               'final_mobile': _convert_phone(job.contact_id.mobile or '', PHONE_COUNTRY_PREFIX),
                               'final_mobile_confidential':'conf' in (job.contact_id.mobile or ''),
                               'final_title': job.function_label or '',
                               'final_categs': job.function_code_label or '',
                               'final_gender': job.contact_id.gender or '',
                               'final_courtesy': job.contact_id.title or '',
                            }
                            selected_jobs.append(new_job)
                if selected_jobs:
                    selected_jobs = sorted(selected_jobs, key=lambda x: x['sequence'])
                new_sequence = 1
                found_g = False
                for new_job in selected_jobs:
                    if new_job['email'] and (not sending_address or (sending_address and not found_g and 'G' in new_job['categs'])):
                        sending_address = new_job['email']
                        sending_courtesy = new_job['final_courtesy']
                        sending_name = new_job['last_name']
                        found_g = ('G' in new_job['categs'])
                    cont_count += 1
                    if new_job['sequence'] <= 5 and new_sequence <= 5:
                        new_job['sequence'] = new_sequence
                    else:
                        new_job['sequence'] = 99
                    cont_proxy_ids = cont_proxy_obj.search([('address_proxy_id', '=', addr_proxy_id), ('job_id', '=', new_job['job_id'])])
                    if cont_proxy_ids:
                        cont_proxy = cont_proxy_ids.read(['sequence', 'last_name', 'first_name', 'email', 'mobile', 'mobile_confidential', 'title', 'categs'])[0]
                        the_same = True
                        for field_name in ['sequence', 'last_name', 'first_name', 'email', 'mobile', 'mobile_confidential', 'title', 'categs']:
                            if cont_proxy[field_name] != new_job[field_name]:
                                the_same = False
                        if not the_same:
                            cont_proxy_ids.write(new_job)
                    else:
                        cont_proxy_obj.create(new_job)
                    new_sequence += 1
                if not sending_address and addr.email and addr.email[0:5] != 'info@':
                    sending_address = addr.email
                    sending_courtesy = 'Cher'
                    sending_name = 'membre'
                if sending_address and addr_proxy_id in modifiable_proxy_ids:
                    addr_proxy_id.write({'sending_address':sending_address, 'sending_name':sending_name, 'sending_courtesy':sending_courtesy})
                    email_count += 1
                else:
                    # adding to the 'no email address text'
                    streets = addr.street or ''
                    if addr.street2:
                        streets += '\n  ' + addr.street2
                    partner_no_email += '\n  Adresse :\n  %s\n  %s' % (streets, (addr.zip_id.name or '') + ' ' + (addr.zip_id.city or ''))
                    if selected_jobs:
                        partner_no_email += '\n    Personnes de contact sans adresse de courriel:'
                        for job in selected_jobs:
                            partner_no_email += '\n    ' + job['final_courtesy'] + ' ' + job['last_name'] + ' ' + job['first_name']
            if addr_proxy_id and addr_proxy_id not in modifiable_proxy_ids:
                modifiable_proxy_ids = modifiable_proxy_ids.append(addr_proxy_id)
        return (partner_no_email, addr_count, modif_count, email_count, cont_count)
     
    @api.model
    def _daily_update(self, new_table=False, raz_exclude=False):
        cronline_id = self.env['cci_logs.cron_line']._start('Memberdirectory_DailyUpdate')
        self.env['cci_logs.cron_line']._addComment(cronline_id, 'Daily updates of the memberdirectory\'s tables\n')
        #
        addr_proxy_obj = self.env['directory.address.proxy']
        cont_proxy_obj = self.env['directory.job.proxy']
        # extract the ID of the website
        obj_user = self.env['res.users']
        website_id = obj_user.search([('name', '=', 'Noomia')])[0].id
        #
        modifiable_proxy_ids = []
        if new_table:
            cont_ids = cont_proxy_obj.search([])
            cont_ids.write({'active': False})
            addr_ids = addr_proxy_obj.search([])
            addr_ids.write({'active': False})
            used_res_partner_address_ids = []
        else:
            existing_addr_ids = addr_proxy_obj.search([])
            existing_addresses = existing_addr_ids.read(['address_id', 'write_uid', 'user_validated', 'internal_validated'])
            used_res_partner_address_ids = [x['address_id'][0] for x in existing_addresses]
            modifiable_proxy_ids = [x['id'] for x in existing_addresses if not x['write_uid'] or (x['write_uid'] and x['write_uid'][0] <> website_id and not x['user_validated'] and not x['internal_validated'])]
        # extract all ids of activity sector categories and remove '[303]' from name
        obj_categ = self.env['res.partner.activsector']
        categ_ids = obj_categ.search([])
        categs = categ_ids.read(['code'])
        dCategs = {}
        dSectCode2ID = {}
        for categ in categs:
            dCategs[categ['id']] = categ['code']
            dSectCode2ID[categ['code']] = categ['id']
        # table for converting old activity sectors to new ones
        dOldSectID2NewID = {}
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['ActivityCodeRootID'])
        if param_values.has_key('ActivityCodeRootID'):
            activityCodeRootID = param_values['ActivityCodeRootID']
            obj_oldcateg = self.env['res.partner.category']
            old_len = 0
            oldcateg_ids = [ activityCodeRootID ]
            while len(oldcateg_ids) > old_len:
                new_ids = oldcateg_ids[old_len:]  # ids of categories added last time
                old_len = len(oldcateg_ids)  # the new frontier ...
                new_categs = new_ids.read(['child_ids'])
                for categ in new_categs:
                    if categ['child_ids']:
                        oldcateg_ids.extend(categ['child_ids'])
            oldcategs = oldcateg_ids.with_context({'lang':'fr_FR'}).read(['name'])
            for oldcateg in oldcategs:
                formated_name = oldcateg['name']
                posA = formated_name.rfind('[')
                posB = formated_name.rfind(']')
                if posA >= 0 and posB > 0 and posA < posB:
                    code = formated_name[posA + 1:posB]
                    if dSectCode2ID.has_key(code):
                        dOldSectID2NewID[oldcateg['id']] = dSectCode2ID[code]
         
        # Extraction of data
        partner_obj = self.env['res.partner']
        addr_obj = self.env['res.partner']
        PHONE_COUNTRY_PREFIX = self.get_phone_country_prefix()
        addr_count = 0
        modif_count = 0
        not_in_directory_count = 0
        cont_count = 0
        email_count = 0
        member_wo_address = []
        partners_wo_emails = ''
        partner_ids = partner_obj.search([('state_id', '=', 1), ('membership_state', 'in', ['free', 'invoiced', 'paid'])])
        # adding the current partners with subscriptions to electronic memberdirectory for full page
        # while keeping their address_ids for setting 'full_page_app'
        full_page_partner_ids = []
        subs_partner_ids = {}
        in_five_days = (datetime.datetime.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        thelastday = datetime.datetime.today().strftime('%Y-%m-%d')
        sub_type_obj = self.env['partner_subscription.type']
        sub_type_ids = sub_type_obj.search([('code', '=', 'SOCREPELEC')])
        subscription_obj = self.env['partner_subscription']
        subscriptions = subscription_obj.search([('type_id', 'in', sub_type_ids.ids), ('state', '=', 'current')])
        for subs in subscriptions:
            if subs.state == 'current' and subs.begin and (subs.begin <= in_five_days) and subs.end and (subs.end >= thelastday) and subs.partner_id:
                if not subs.partner_id.dir_exclude:
                    if subs.partner_id.id not in partner_ids:
                        partner_ids.append(subs.partner_id.id)
                    if subs.partner_id.id not in subs_partner_ids:
                        data_sub = {
                            'id':subs.partner_id.id,
                            'amount':subs.price,
                            'begindate':subs.begin,
                            'enddate':subs.end,
                        }
                        subs_partner_ids[subs.partner_id.id] = data_sub
                    else:
                        data_sub = subs_partner_ids[subs.partner_id.id]
                        data_sub['amount'] += subs.price
                        data_sub['begindate'] = min(data_sub['begindate'], subs.begin)
                        data_sub['enddate'] = max(data_sub['enddate'], subs.end)
                        subs_partner_ids[subs.partner_id.id] = data_sub
        for (partner_id, data_sub) in subs_partner_ids.items():
            full_page_partner_ids.append(partner_id)
            if data_sub['amount'] > 0.001 and partner_id not in partner_ids:
                partner_ids.append(partner_id)
        # adding the current freemium members with subscriptions to electronic memberdirectory for full page
        # while keeping their address_ids for setting 'full_page_app'
        full_page_contact_ids = []
        subs_contact_partner_ids = {}
        in_five_days = (datetime.datetime.today() + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        thelastday = datetime.datetime.today().strftime('%Y-%m-%d')
        sub_type_obj = self.env['premium_subscription.type']
        sub_type_ids = sub_type_obj.search([('code', '=', 'REPMEMBRE')])
        subscription_obj = self.env['premium_subscription']
        subscriptions = subscription_obj.search([('type_id', 'in', sub_type_ids), ('state', '=', 'current')])
        for subs in subscriptions:
            if subs.state == 'current' and subs.begin and (subs.begin <= in_five_days) and subs.end and (subs.end >= thelastday) and subs.contact_id and subs.contact_id.job_ids:
                for possible_job in subs.contact_id.job_ids:
                    if possible_job.address_id and not possible_job.address_id.dir_exclude and possible_job.address_id.active and possible_job.address_id.partner_id \
                        and not possible_job.address_id.partner_id.dir_exclude and possible_job.address_id.partner_id.state_id.id == 1 and possible_job.address_id.partner_id.active:
                            if subs.partner_id.id not in partner_ids:
                                partner_ids.append(subs.partner_id.id)
                            if subs.partner_id.id not in subs_contact_partner_ids:
                                data_sub = {
                                    'id':possible_job.address_id.partner_id.id,
                                    'amount':subs.price,
                                    'begindate':subs.begin,
                                    'enddate':subs.end,
                                }
                                subs_contact_partner_ids[possible_job.address_id.partner_id.id] = data_sub
                            else:
                                data_sub = subs_contact_partner_ids[possible_job.address_id.partner_id.id]
                                data_sub['amount'] += subs.price
                                data_sub['begindate'] = min(data_sub['begindate'], subs.begin)
                                data_sub['enddate'] = max(data_sub['enddate'], subs.end)
                                subs_contact_partner_ids[possible_job.address_id.partner_id.id] = data_sub
        for (partner_id, data_sub) in subs_contact_partner_ids.items():
            full_page_partner_ids.append(partner_id)
            if data_sub['amount'] > 0.001 and partner_id not in partner_ids:
                partner_ids.append(partner_id)
        #
        partners = partner_obj.browse(partner_ids, {'lang':'fr_FR'})
        for partner in partners:
            if partner.address:
                partner_no_email = ''
                for addr in partner.child_ids:
                    if addr.dir_exclude and raz_exclude:
                        correction = {'dir_exclude':False}
                        addr.write(correction)
                        not_in_directory_count += 1
                    (errors, res_addr_count, res_modif_count, res_email_count, res_cont_count) = addr_proxy_obj._synchro_address(addr, partner, modifiable_proxy_ids, full_page_partner_ids, new_table, website_id, dCategs, dSectCode2ID, dOldSectID2NewID, oldcateg_ids)
                    if errors:
                        partner_no_email = '\n-----------------------------\nPartenaire : %s [%s] %s' % (partner.name, partner.id, errors)
                        partners_wo_emails += partner_no_email
                    addr_count += res_addr_count
                    modif_count += res_modif_count
                    email_count += res_email_count
                    cont_count += res_cont_count
 
            else:
                member_wo_address.append(partner.id)
        results = 'Selected Partners : %s\nPublished Addresses : %s\nDirectory Exclude cleaned : %s\nContacts found : %s\nEmail Count : %s\nMembers without addresses : [%s]' % (str(len(partner_ids)),
                                                                                                                                               str(addr_count),
                                                                                                                                               str(not_in_directory_count),
                                                                                                                                               str(cont_count),
                                                                                                                                               str(email_count),
                                                                                                                                               ','.join([str(x) for x in member_wo_address]))
        self.env['cci_logs.cron_line']._addComment(cronline_id, results)
        self.env['cci_logs.cron_line']._stop(cronline_id, True, '\n---end---')
        return True

class directory_job_proxy(models.Model):
    _name = 'directory.job.proxy'
    _description = "proxy job 4 yearly directory"
    
    @api.model
    def _title_get(self):
        obj = self.env['res.partner.title']
        ids = obj.search([])
        res = obj.read(['shortcut', 'name', 'domain'])
        res = [(r['shortcut'], r['name']) for r in res if r['domain'] == 'contact']
        return res
    
    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.contact_id.name + ' ' + (record.contact_id.first_name or '')
            res.append((record['id'], name))
        return res

    address_proxy_id = fields.Many2one('directory.address.proxy', 'Partner Proxy', required=True, ondelete='cascade')
    address_id = fields.Many2one('res.partner', 'Address')
    job_id = fields.Many2one('res.partner', 'Job')
    contact_id = fields.Many2one('res.partner', 'Contact')
    sequence = fields.Integer('Sequence', required=True)
    last_name = fields.Char('Name', size=30)
    first_name = fields.Char('First Name', size=30)
    email = fields.Char('EMail', size=240)
    mobile = fields.Char('Mobile', size=40)
    mobile_confidential = fields.Boolean('Mobile confidential')
    title = fields.Char('Title', size=250)
    # 'birthdate =fields.date('Birthdate')
    # 'linkedin_url =fields.Char('LinkedIN',size=200)
    categs = fields.Char('Categs', size=10)
    new_sequence = fields.Integer('New Sequence')
    new_last_name = fields.Char('New Name', size=30)
    new_first_name = fields.Char('New First Name', size=30)
    new_email = fields.Char('New EMail', size=240)
    new_mobile = fields.Char('New Mobile', size=40)
    new_mobile_confidential = fields.Boolean('New Mobile confidential')
    new_title = fields.Char('New Title', size=250)
    # 'new_birthdate =fields.date('New Birthdate'),
    # 'new_linkedin_url =fields.Char('New LinkedIN',size=200),
    final_last_name = fields.Char('Final Name', size=30)
    final_first_name = fields.Char('Final First Name', size=30)
    final_email = fields.Char('Final EMail', size=240)
    final_mobile = fields.Char('Final Mobile', size=40)
    final_mobile_confidential = fields.Boolean('Final Mobile confidential')
    final_title = fields.Char('Final Title', size=250)
    final_sequence = fields.Integer('Final Sequence')
    # 'final_birthdate =fields.date('Final Birthdate'),
    # 'final_linkedin_url =fields.Char('Final LinkedIN',size=200),
    final_courtesy = fields.Selection(selection='_title_get', string='Final Title')
    final_gender = fields.Selection([('man', 'Man'), ('women', 'Women')], "Final Gender")
    final_categs = fields.Char('Final Categs', size=10)
    internal_validated = fields.Boolean('Internal Validated')
    new_record = fields.Boolean('New Contact')
    change_date = fields.Datetime('Change Date')
    marked_for_deletion = fields.Boolean('Marked For Deletion')
    active = fields.Boolean('Active', default=True)

    @api.multi
    def write(self, vals):
        current = self
        if vals.has_key('job_id'):
            if not vals['job_id']:
                vals.update({
                    'new_record':True,
                    'final_last_name':vals.get('new_last_name', ''),
                    'final_first_name':vals.get('new_first_name', ''),
                    'final_email':vals.get('new_email', ''),
                    'final_title':vals.get('new_title', ''),
                    'final_categs':'',
                    'final_gender':'man',
                    'final_courtesy':'Monsieur',
                })
            else:
                if not vals.has_key('contact_id'):
                    job = self.env['res.partner'].browse(vals['job_id'])
                    vals.update({'contact_id':job.contact_id.id})
        if vals.has_key('new_last_name'):
            vals.update({'final_last_name':vals['new_last_name']})
        if vals.has_key('new_first_name'):
            vals.update({'final_first_name':vals['new_first_name'].title()})
        if vals.has_key('new_email'):
            vals.update({'final_email':vals['new_email']})
        if vals.has_key('new_sequence'):
            vals.update({'final_sequence':vals['new_sequence']})
        if vals.has_key('new_title'):
            vals.update({'final_title':vals['new_title']})
        if vals.has_key('new_mobile'):
            vals.update({'final_mobile':_only_digits(vals['new_mobile'] or '')})
        if vals.has_key('new_mobile_confidential'):
            vals.update({'final_mobile_confidential':vals['new_mobile_confidential']})
        vals.update({'internal_validated':False})
        return super(osv.osv, self).write(vals)

class directory_job2delete(models.Model):
    _name = "directory.job2delete"
    _description = "initial jobs marked for deletion"
        
    address_proxy_id = fields.Many2one('directory.address.proxy', 'Partner Proxy', ondelete='cascade')
    job_id = fields.Integer('Job ID')
    last_name = fields.Char('Last Name', size=50)
    first_name = fields.Char('First Name', size=50)
    active = fields.Boolean('Active', default=True)
    
    @api.model        
    def create(self, vals):
        if vals.has_key('job_id'):
            job_ids = self.env['directory.job.proxy'].search([('job_id', '=', vals['job_id'])], limit=1)
            if job_ids:
                job = job_ids.read(['address_proxy_id', 'last_name', 'first_name'])
                vals.update({'address_proxy_id': job['address_proxy_id'][0], 'last_name': job['last_name'] or '', 'first_name': job['first_name'] or ''})
        return super(directory_job2delete, self).create(vals)

class directory_complex(models.Model):
    _name = "directory.complex"
    _description = 'Partner ID of complex cases to isolate them from simple ones'
   
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)

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
from openerp import models, fields, api ,tools , _
from openerp.exceptions import Warning
import datetime
import string
from operator import itemgetter

def _upper_accent(string):
    result = string.replace(u'à','A').replace(u'â','A').replace(u'ä','A').replace(u'ç','C').replace(u'é','E').replace(u'è','E').replace(u'ê','E').replace(u'ë','E')
    result = result.replace(u'î','I').replace(u'ï','I').replace(u'ô','O').replace(u'ö','O').replace(u'ù','U').replace(u'û','U').replace(u'ü','U')
    result = result.replace(u'À','A').replace(u'Â','A').replace(u'Ä','A').replace(u'É','E').replace(u'È','E').replace(u'Ê','E').replace(u'Ë','E')
    result = result.replace(u'Î','I').replace(u'Ï','I').replace(u'Ô','O').replace(u'Ö','O').replace(u'Ù','U').replace(u'Û','U').replace(u'Ü','U')
    result = result.upper()
    return result
    
def _title_accent(string):
    if string:
        index = 0
        first_letter = True
        result = u''
        while index < len(string):
            carac = string[index]
            if first_letter:
                carac = _upper_accent(carac)
            else:
                carac = carac.lower()
            first_letter = False
            if carac in ' -,.':
                first_letter = True
            result += carac
            index += 1
        if result.find(u' De ') > -1:
            result = result.replace(u' De ',u' de ')
        if result.find(u' DE ') > -1:
            result = result.replace(u' DE ',u' de ')
        if result.find(u' Du ') > -1:
            result = result.replace(u' Du ',u' du ')
        if result.find(u' DU ') > -1:
            result = result.replace(u' DU ',u' du ')
        if result.find(u' Des ') > -1:
            result = result.replace(u' Des ',u' des ')
        if result.find(u' DES ') > -1:
            result = result.replace(u' DES ',u' des ')
        if result.find(u' DeS ') > -1:
            result = result.replace(u' DeS ',u' des ')
        if result.find(u' DEs ') > -1:
            result = result.replace(u' DEs ',u' des ')
        if result.find(u' D\'') > -1:
            result = result.replace(u' D\'',u' d\'')
        if result.find(u' La ') > -1:
            result = result.replace(u' La ',u' la ')
        if result.find(u' LA ') > -1:
            result = result.replace(u' LA ',u' la ')
    else:
        result = ''
    return result

def _clean_api(string):
    # In some cases, the API used to verify vat number give a result in more than a HTML line. We must correct this
    value = string
    pos = value.find('<BR/>')
    if pos > 0:
        value = value[0:pos]
    return value

def _only_digits(string):
    result = ''
    for carac in string:
        if carac.isdigit():
            result += carac
    return result

def _check_phone_num(phone=''):
    if not phone:
        return ''
    result = phone.strip()
    if result and result[0:1] == '+':
        result = '00'+result[1:]
    result = _only_digits(result)
    GSM_PREFIX = ['0470','0471','0472','0473','0474','0475','0476','0477','0478','0479','0484','0485','0486','0487','0488','0489','0492','0493','0494','0495','0496','0497','0498','0499']
    if not result.startswith('00'):
        is_gsm = False
        for item in GSM_PREFIX:
            is_gsm = phone.startswith(item)
            if is_gsm:
                break
        if is_gsm:
            if not len(result) == 10:
                result = ''
        else:
            if not len(result) == 9:
                result = ''
    return result

def _check_email(email=''):
    result = ''
    if email:
        result = email.strip().lower().replace(' ','')
        if '@' in result:
            (part1,part2) = result.split('@')
            if part1 and part2 and len(part2) > 0 and len(part1) > 1 and not ('@' in part2):
                last_pos = part2.rfind('.')
                if last_pos > 0:
                    part3 = part2[last_pos+1:]
                    part2 = part2[:last_pos]
                    if len(part2)> 1: # forget the control of the length of the domain : too many exceptions
                        pass
                    else:
                        result = ''
                else:
                    result = ''
            else:
                result = ''
        else:
            result = ''
    return result

def _is_mail_personal_domain(email):
    #TODO in parameters or table
    parts = email.split('@')
    if len(parts) == 2:
        #print 'domain'
        #print parts[1]
        if parts[1].lower() in ['gmail.com','skynet.be','hotmail.com','scarlet.be','me.com','msn.com','outlook.com','yahoo.fr']:
            return True
        else:
            return False
    else:
        return False

def _create_new_partner(self,premium_company):
    #print 'creation partner'
    partner_id = 0
    if not premium_company.partner_id:
        #print 'inside 1'
        partner_obj = self.env['res.partner']
        if premium_company.company_num:
            #print 'inside 2'
            # check if it don't exists NOW
            partner_ids = partner_obj.search([('vat','=',premium_company.company_num.upper())])
            if partner_ids:
                partner_id = partner_ids[0]
        if not partner_id and premium_company.company_name:
            #print 'inside 3'
            # check if it don't exists NOW
            partner_ids = partner_obj.search([('name','=',_clean_api(_upper_accent(premium_company.company_name)))])
            if partner_ids:
                #print 'search address'
                partners = partner_ids #partner_obj.browse(cr,uid,partner_ids)
                for possible_partner in partners:
                    if possible_partner.child_ids:
                        for addr in possible_partner.child_ids:
                            if _upper_accent(addr.street) == _upper_accent(premium_company.street): ## TODO ZIP CODE
                                partner_id = possible_partner.id
                                break
                            else:
                                if addr.other_contact_ids:
                                    for job in addr.other_contact_ids:
                                        #print _upper_accent(job.contact_id.name) + ' =? ' + _upper_accent(premium_company.premium_contact_id.last_name)
                                        if job.contact_id and (_upper_accent(job.contact_id.name) == _upper_accent(premium_company.premium_contact_id.last_name)) and \
                                                (_title_accent(job.contact_id.first_name) == _title_accent(premium_company.premium_contact_id.first_name)):
                                            partner_id = possible_partner.id
                                            break
                                    if partner_id:
                                        break
        if partner_id:
            # not creation; updating
            premium_company.write({'partner_id':partner_id})
#             company_premium = company_premium.browse(cr,uid,[company_premium.id])[0]
            _update_partner(self,premium_company)
        else:
            # real creation
            vals = {}
            vals['name'] = _clean_api(_upper_accent(premium_company.company_name))
            if premium_company.company_num:
                vals['vat'] = _upper_accent(premium_company.company_num)
            if premium_company.company_status:
                vals['title'] = premium_company.company_status ## TODO check if title exist
            if premium_company.employee:
                vals['employee_slice'] = premium_company.employee  ## TODO check if CM decision confirmed or clearly indicated on form's side
            vals['can_check_formation'] = premium_company.check_formation
            vals['international_company'] = premium_company.international
            #vals['formation_priority'] = premium_company.prio_formation
            #vals['formation_invest'] = premium_company.invest_formation
            vals['equal_representation'] = premium_company.equal_representation
            vals['activity_description'] = premium_company.activity_description
            #print 'vals'
            #print vals
            partner_id = partner_obj.create(vals).id
    return partner_id

def _update_partner(self,premium_company):
    #print 'Update partner'
    partner_obj = self.env['res.partner']
    old_values = premium_company.partner_id.with_context({'lang':'fr_FR'}).read(['name','vat','title','employee_slice','can_check_formation','international_company','equal_representation','activity_description','membership_state'])[0]
    vals = {}
    vals['name'] = _clean_api(_upper_accent(premium_company.company_name))
    if premium_company.company_num:
        vals['vat'] = _upper_accent(premium_company.company_num)
    if premium_company.company_status:
        title = self.env['res.partner.title'].search([('name','=',premium_company.company_status)])
        vals['title'] = title and title[0].id or False
    if premium_company.employee:
        vals['employee_slice'] = premium_company.employee  ## TODO check if CM decision confirmed or clearly indicated on form's side
    vals['can_check_formation'] = premium_company.check_formation
    vals['international_company'] = premium_company.international
    vals['equal_representation'] = premium_company.equal_representation
    if premium_company.activity_description and not old_values['activity_description']:
        vals['activity_description'] = premium_company.activity_description
    if (old_values['name'] <> vals['name']) and (old_values['membership_state'] in ['free','invoiced','paid']):
        parameter_obj = self.env['ir.config_parameter']
        param_values = parameter_obj.get_param('PremiumFormSupervisors')
        if param_values:
            email_managers = param_values #param_values['PremiumFormSupervisors']
        else:
            email_managers = ['fb@ccilvn.be']
        if email_managers:
            email_content = u"""<p>En injectant les données d'un formulaire nous avons changé le nom d'un de nos membres [%i]:<br/>
                                Ancien nom : <b>%s</b><br/>
                                Nouveau Nom : <b>%s</b></p>
            """ % (old_values['id'],old_values['name'],vals['name'])
            tools.email_send('noreply@ccilvn.be', email_managers, 'Chg nom Membre par un formulaire Premium', email_content, subtype='html')
    premium_company.partner_id.with_context({'lang':'fr_FR'}).write(vals)
    return True

def _create_new_address_classic(self,premium_company):
    if premium_company.partner_id and not premium_company.address_id:
        vals = {'partner_id':premium_company.partner_id.id}
        # determination of address's type
        addr_type = 'default'
        if premium_company.partner_id.child_ids:
            for addr in premium_company.partner_id.child_ids:
                if addr.type == 'default':
                    addr_type = 'other'
                    break
        vals['type'] = addr_type
        #
        if premium_company.street:
            vals['street'] = _upper_accent(premium_company.street)
        if premium_company.zip_code and premium_company.zip_name:
            zip_id = 0
            zip_obj = self.env['res.partner.zip']
            zip_ids = zip_obj.search([('name','=',premium_company.zip_code)])
            if zip_ids >= 1:
                zips = zip_ids.read(['id','name','city','other_names'])
                for czip in zips:
                    if czip['city'].upper() == _upper_accent(premium_company.zip_name.strip()):
                        zip_id = czip['id']
                    else:
                        if czip['other_names'] and ( _upper_accent(premium_company.zip_name.strip()) in czip['other_names'] ):
                            zip_id = czip['id']
            if zip_id:
                vals['zip_id'] = zip_id      
        if premium_company.phone and not premium_company.street_work:
            vals['phone'] = _check_phone_num(premium_company.phone)
        if premium_company.fax and not premium_company.street_work:
            vals['fax'] = _check_phone_num(premium_company.fax)
        if premium_company.zoning and not premium_company.street_work:
            vals['zoning'] = premium_company.zoning
        # validation of activity sectors from 'code'
        sector_codes = []
        if premium_company.sector1:
            sector_codes.append(premium_company.sector1)
        if premium_company.sector2:
            sector_codes.append(premium_company.sector2)
        if premium_company.sector3:
            sector_codes.append(premium_company.sector3)
        current_sector = 0
        while sector_codes:
            sector_code = sector_codes.pop(0)
            activsector_obj = self.env['res.partner.activsector']
            sector_ids = activsector_obj.search([('code','=',sector_code)])
            if sector_ids and len(sector_ids) == 1:
                current_sector += 1
                vals['sector'+str(current_sector)] = sector_ids[0]
        vals['activity_description'] = premium_company.activity_description
        address_obj = self.env['res.partner']
        address_id = address_obj.create(vals).id
        if address_id and not premium_company.partner_id.user_id and addr_type == 'default' and vals.has_key('zip_id'):
            # select the default salesman
            data = self.env['res.partner.zip'].browse(vals['zip_id'])
            saleman_id = data.user_id and data.user_id.id or False
            if saleman_id:
                premium_company.partner_id.write({'user_id':saleman_id})
    else:
        address_id = 0
    return address_id

def _create_new_address_work(self,premium_company):
    if premium_company.partner_id and not premium_company.address_work_id and premium_company.street_work:
        vals = {'partner_id':premium_company.partner_id.id}
        vals['type'] = 'other'
        if premium_company.street_work:
            vals['street'] = _upper_accent(premium_company.street_work)
        if premium_company.zip_code_work and premium_company.zip_name_work:
            zip_id = 0
            zip_obj = self.env['res.partner.zip']
            zip_ids = zip_obj.search([('name','=',premium_company.zip_code_work)])
            if zip_ids >= 1:
                zips = zip_ids.read(['id','name','city','other_names'])
                for czip in zips:
                    if czip['city'].upper() == _upper_accent(premium_company.zip_name_work):
                        zip_id = czip['id']
                    else:
                        if czip['other_names'] and ( _upper_accent(premium_company.zip_name_work) in czip['other_names'] ):
                            zip_id = czip['id']
            if zip_id:
                vals['zip_id'] = zip_id      
        if premium_company.phone:
            vals['phone'] = _check_phone_num(premium_company.phone)
        if premium_company.fax:
            vals['fax'] = _check_phone_num(premium_company.fax)
        if premium_company.zoning:
            vals['zoning'] = premium_company.zoning
        # validation of activity sectors from 'code'
        sector_codes = []
        if premium_company.sector1:
            sector_codes.append(premium_company.sector1)
        if premium_company.sector2:
            sector_codes.append(premium_company.sector2)
        if premium_company.sector3:
            sector_codes.append(premium_company.sector3)
        current_sector = 0
        while sector_codes:
            sector_code = sector_codes.pop(0)
            activsector_obj = self.env['res.partner.activsector']
            sector_ids = activsector_obj.search([('code','=',sector_code)])
            if sector_ids and len(sector_ids) == 1:
                current_sector += 1
                vals['sector'+str(current_sector)] = sector_ids[0]
        vals['activity_description'] = premium_company.activity_description
        address_obj = self.env['res.partner']
        address_work_id = address_obj.create(vals).id
    else:
        address_work_id = False
    return address_work_id

def _update_address(self,premium_company):
    vals = {'partner_id':premium_company.partner_id.id}
    if premium_company.street:
        vals['street'] = _upper_accent(premium_company.street)
    if premium_company.zip_code and premium_company.zip_name:
        zip_id = 0
        zip_obj = self.env['res.partner.zip']
        zip_ids = zip_obj.search([('name','=',premium_company.zip_code)])
        if zip_ids >= 1:
            zips = zip_ids.read(['id','name','city','other_names'])
            for czip in zips:
                if czip['city'].upper() == _upper_accent(premium_company.zip_name):
                    zip_id = czip['id']
                else:
                    if czip['other_names'] and ( _upper_accent(premium_company.zip_name) in czip['other_names'] ):
                        zip_id = czip['id']
        if zip_id:
            vals['zip_id'] = zip_id      
    if premium_company.phone:
        vals['phone'] = _check_phone_num(premium_company.phone)
    if premium_company.fax:
        vals['fax'] = _check_phone_num(premium_company.fax)
    if premium_company.zoning:
        vals['zoning'] = premium_company.zoning
    # validation of activity sectors from 'code'
    sector_codes = []
    if premium_company.sector1:
        sector_codes.append(premium_company.sector1)
    if premium_company.sector2:
        sector_codes.append(premium_company.sector2)
    if premium_company.sector3:
        sector_codes.append(premium_company.sector3)
    current_sector = 0
    while sector_codes:
        sector_code = sector_codes.pop(0)
        activsector_obj = self.env['res.partner.activsector']
        sector_ids = activsector_obj.search([('code','=',sector_code)])
        if sector_ids and len(sector_ids) == 1:
            current_sector += 1
            vals['sector'+str(current_sector)] = sector_ids[0]
    vals['activity_description'] = premium_company.activity_description
    address_obj = self.env['res.partner']
    premium_company.address_id.write(vals)
    return True

def _update_working_address(self,premium_company):
    vals = {'partner_id':premium_company.partner_id.id}
    if premium_company.street_work:
        vals['street'] = _upper_accent(premium_company.street_work)
    if premium_company.zip_code_work and premium_company.zip_name_work:
        zip_id = 0
        zip_obj = self.env['res.partner.zip']
        zip_ids = zip_obj.search([('name','=',premium_company.zip_code_work)])
        if zip_ids >= 1:
            zips = zip_ids.read(['id','name','city','other_names'])
            for czip in zips:
                if czip['city'].upper() == _upper_accent(premium_company.zip_name_work):
                    zip_id = czip['id']
                else:
                    if czip['other_names'] and ( _upper_accent(premium_company.zip_name_work) in czip['other_names'] ):
                        zip_id = czip['id']
        if zip_id:
            vals['zip_id'] = zip_id      
    if premium_company.phone:
        vals['phone'] = _check_phone_num(premium_company.phone)
    if premium_company.fax:
        vals['fax'] = _check_phone_num(premium_company.fax)
    if premium_company.zoning:
        vals['zoning'] = premium_company.zoning
    # validation of activity sectors from 'code'
    sector_codes = []
    if premium_company.sector1:
        sector_codes.append(premium_company.sector1)
    if premium_company.sector2:
        sector_codes.append(premium_company.sector2)
    if premium_company.sector3:
        sector_codes.append(premium_company.sector3)
    current_sector = 0
    while sector_codes:
        sector_code = sector_codes.pop(0)
        activsector_obj = self.env['res.partner.activsector']
        sector_ids = activsector_obj.search([('code','=',sector_code)])

        if sector_ids and len(sector_ids) == 1:
            current_sector += 1
            vals['sector'+str(current_sector)] = sector_ids[0]
    vals['activity_description'] = premium_company.activity_description
    address_obj = self.env['res.partner']
    premium_company.address_work_id.write(vals)
    return True

def _update_contact_fields(self,premium_contact,vals):
    if premium_contact.sex == 'Mme':
        vals['gender'] = 'women'
        title = self.env['res.partner.title'].search([('name','=','Madame')])
        vals['title'] = title and title[0].id or False
    else:
        vals['gender'] = 'man'
        title = self.env['res.partner.title'].search([('name','=','Madame')])
        vals['title'] = title and title[0].id or False

    if premium_contact.mobile:
        vals['mobile'] = _check_phone_num(premium_contact.mobile)
    if premium_contact.birthdate:
        vals['birthdate'] = premium_contact.birthdate
    vals['pf_zip_code'] = premium_contact.zip_code
    vals['pf_linkedin'] = premium_contact.li
    vals['pf_twitter'] = premium_contact.tw
    vals['pf_facebook'] = premium_contact.fb
    vals['pf_linkedin_freq'] = premium_contact.freq_li
    vals['pf_twitter_freq'] = premium_contact.freq_tw
    vals['pf_facebook_freq'] = premium_contact.freq_fb
    vals['pf_smartphone'] = premium_contact.smartphone
    vals['pf_smart_info'] = premium_contact.smart_info
    vals['pf_tablet'] = premium_contact.tablet
    vals['pf_tablet_press'] = premium_contact.tablet_press
    vals['pf_app_pro'] = premium_contact.app_pro
    vals['pf_invit_mail'] = premium_contact.invit_mail
    vals['pf_invit_network'] = premium_contact.invit_network
    vals['pf_invit_post'] = premium_contact.invit_post
    vals['pf_sms'] = premium_contact.sms
    vals['pf_ecustomer'] = premium_contact.ecustomer
    vals['pf_pay_creditcard'] = premium_contact.pay_creditcard
    vals['pf_care_cci'] = premium_contact.care_cci
    vals['pf_eleccar'] = premium_contact.eleccar
    vals['pf_use_language'] = premium_contact.use_language
    vals['pf_nighter'] = premium_contact.nighter
    vals['pf_children'] = premium_contact.children
    vals['pf_want_invest'] = premium_contact.want_invest
    vals['pf_owner'] = premium_contact.owner
    vals['pf_cluber'] = premium_contact.cluber
    vals['pf_club_cw'] = premium_contact.club_cw
    vals['pf_club_cl'] = premium_contact.club_cl
    vals['pf_club_bni'] = premium_contact.club_bni
    vals['pf_club_apm'] = premium_contact.club_apm
    vals['pf_club_gceq'] = premium_contact.club_gceq
    vals['pf_club_ypowpo'] = premium_contact.club_ypowpo
    vals['pf_club_far'] = premium_contact.club_far
    vals['pf_club_fce'] = premium_contact.club_fce
    vals['pf_club_new'] = premium_contact.club_new
    vals['pf_club_zoning'] = premium_contact.club_zoning
    vals['pf_club_golf'] = premium_contact.club_golf
    vals['pf_club_sc'] = premium_contact.club_sc
    vals['pf_club_other'] = premium_contact.club_other
    if premium_contact.club_other_names:
        vals['pf_club_other_names'] = premium_contact.club_other_names
    vals['pf_networker'] = premium_contact.networker
    vals['pf_freq_network'] = premium_contact.freq_network
    vals['pf_network_morning'] = premium_contact.network_morning
    vals['pf_network_lunch'] = premium_contact.network_lunch
    vals['pf_network_dinner'] = premium_contact.network_dinner
    vals['pf_network_night'] = premium_contact.network_night
    vals['pf_conf_8_10'] = premium_contact.conf_8_10
    vals['pf_conf_9_11'] = premium_contact.conf_9_11
    vals['pf_conf_10_12'] = premium_contact.conf_10_12
    vals['pf_conf_12_14'] = premium_contact.conf_12_14
    vals['pf_conf_14_16'] = premium_contact.conf_14_16
    vals['pf_conf_18_20'] = premium_contact.conf_18_20
    vals['pf_dispo_mon_morning'] = premium_contact.dispo_mon_morning
    vals['pf_dispo_mon_lunch'] = premium_contact.dispo_mon_lunch
    vals['pf_dispo_mon_evening'] = premium_contact.dispo_mon_evening
    vals['pf_dispo_tue_morning'] = premium_contact.dispo_tue_morning
    vals['pf_dispo_tue_lunch'] = premium_contact.dispo_tue_lunch
    vals['pf_dispo_tue_evening'] = premium_contact.dispo_tue_evening
    vals['pf_dispo_wed_morning'] = premium_contact.dispo_wed_morning
    vals['pf_dispo_wed_lunch'] = premium_contact.dispo_wed_lunch
    vals['pf_dispo_wed_evening'] = premium_contact.dispo_wed_evening
    vals['pf_dispo_thu_morning'] = premium_contact.dispo_thu_morning
    vals['pf_dispo_thu_lunch'] = premium_contact.dispo_thu_lunch
    vals['pf_dispo_thu_evening'] = premium_contact.dispo_thu_evening
    vals['pf_dispo_fri_morning'] = premium_contact.dispo_fri_morning
    vals['pf_dispo_fri_lunch'] = premium_contact.dispo_fri_lunch
    vals['pf_dispo_fri_evening'] = premium_contact.dispo_fri_evening
    vals['pf_dispo_sat_morning'] = premium_contact.dispo_sat_morning
    vals['pf_dispo_sat_lunch'] = premium_contact.dispo_sat_lunch
    vals['pf_dispo_sat_evening'] = premium_contact.dispo_sat_evening
    vals['pf_dispo_sun_morning'] = premium_contact.dispo_sun_morning
    vals['pf_dispo_sun_lunch'] = premium_contact.dispo_sun_lunch
    vals['pf_dispo_sun_evening'] = premium_contact.dispo_sun_evening
    vals['pf_size_25'] = premium_contact.size_25
    vals['pf_size_2550'] = premium_contact.size_2550
    vals['pf_size_50100'] = premium_contact.size_50100
    vals['pf_size_100'] = premium_contact.size_100
    vals['pf_price_event'] = premium_contact.price_event
    vals['premium_login'] = premium_contact.login
    vals['premium_mp'] = premium_contact.mot_passe
    vals['premium_begin'] = datetime.date.today().strftime('%Y-%m-%d')
    return vals

def _update_job_fields(premium_contact,premium_company,vals):
    if premium_contact.email and not _is_mail_personal_domain(premium_contact.email):
        vals['email'] = _check_email(premium_contact.email)
    if premium_company.person_statut:
        if premium_company.person_statut == 'independent':
            if premium_company.inde_statut:
                if premium_company.inde_statut == 'physical':
                    vals['personal_statut'] = 'ind_physical'
                elif premium_company.inde_statut == 'manager':
                    vals['personal_statut'] = 'ind_manager'
                elif premium_company.inde_statut == 'management':
                    vals['personal_statut'] = 'ind_management'
                elif premium_company.inde_statut == 'professional':
                    vals['personal_statut'] = 'ind_professional'
        else:
            vals['personal_statut'] = 'employee'
    #vals['main_direction'] = premium_company.main_dir
    if premium_company.main_dir:
        categs = 'G'
    else:
        categs = ''
    if premium_company.main_dir_type:
        vals['type_direction'] = premium_company.main_dir_type
        if premium_company.main_dir_type in ['onlydir','majority','associated']:
            categs += '$K'
    if premium_company.main_dir_arrival:
        vals['type_purchase'] = premium_company.main_dir_arrival
    vals['year_purchase'] = premium_company.main_dir_year
    if premium_company.buy_from:
        vals['from_purchase'] = premium_company.buy_from
    if premium_company.shareholder:
        vals['shareholder_count'] = premium_company.shareholder
    vals['share_invest'] = premium_company.invest
    vals['share_investor'] = premium_company.investor
    vals['share_crowdfund'] = premium_company.crowdfund
    vals['share_family'] = premium_company.family
    vals['executive_committee'] = premium_company.steering
    if premium_company.main_dir_type or premium_company.steering:
        vals['decision_level'] = 'direction'
    if premium_company.decision_level:
        vals['decision_level'] = premium_company.decision_level
    if premium_company.purchase:
        categs += 'A'
    if premium_company.administration:
        categs += 'B'
    if premium_company.commercial:
        categs += 'C'
    if premium_company.communication:
        categs += 'U'
    if premium_company.public_relation:
        categs += 'R'
    if premium_company.energy:
        categs += 'VW'
    if premium_company.export:
        categs += 'L'
    if premium_company.finance:
        categs += 'F'
    if premium_company.it:
        categs += 'I'
    if premium_company.logistic:
        categs += 'Z'
    if premium_company.marketing:
        categs += 'M'
    if premium_company.operations:
        categs += 'X'
    if premium_company.production:
        categs += '7'
    if premium_company.projects:
        categs += '8'
    if premium_company.r_d:
        categs += 'H'
    if premium_company.hr:
        categs += 'E'
    if premium_company.secretary:
        categs += 'S'
    if premium_company.security:
        categs += 'Y'
    if premium_company.technical:
        categs += 'T'
    if premium_company.web:
        categs += '@'
    if premium_company.others:
        categs += '#'
    vals['others_name'] = premium_company.others_name
    vals['function_code_label'] = categs
    if premium_company.title:
        vals['function_label'] = _title_accent(premium_company.title)
    #print 'function vals'
    #print vals
    vals['sequence_contact'] = premium_company.importance
    return vals    

def _inject_job(self,premium_company,premium_contact):
    #print 'inside inject job'
    if premium_company.job_id:
        job_id = premium_company.job_id
        # update of job
        #print 'updating job in inject job'
        vals = {}
        vals = _update_job_fields(premium_contact,premium_company,vals)
        #print 'vals'
        #print vals
#         job_obj = self.env['res.partner.job')
        job_id.write(vals)
    else:
        if premium_company.street_work:
            right_address_id = premium_company.address_work_id and premium_company.address_work_id.id
        else:
            right_address_id = premium_company.address_id and premium_company.address_id.id
        if right_address_id and premium_contact.contact_id:
            job_obj = self.env['res.partner']
            job_ids = job_obj.search([('contact_id','=',premium_contact.contact_id.id)])
            if job_ids:

                job_id = job_ids[0]
                # update of existing job
                #print 'updating job in inject part II'
                # update of current job
                vals = {}
                vals = _update_job_fields(premium_contact,premium_company,vals)
                job_id.write(vals)
            else:
                # creation of new job
                #print 'creating job inside inject job'
                vals = {'contact_id':premium_contact.contact_id.id,'address_id':right_address_id}
                vals = _update_job_fields(premium_contact,premium_company,vals)
                job_id = job_obj.create(vals).id
                if not job_id:
                    job_id = 0
        else:
            job_id = 0
    return job_id

def _mark_as_injected(self,premium_contact):
    if premium_contact.state in ['partial']:
        # check if not totally injected now : we refresh the object then check if all premium_companies are injected
        premium_contact_id = premium_contact.id
        premium_contact_obj = self.env['premium_contact']
        fresh_premium_contact = premium_contact #premium_contact_obj.browse(cr,uid,[premium_contact_id])[0]
        all_injected = True
        for premium_company in fresh_premium_contact.premium_company_ids:
            if premium_company.state <> 'injected':
                all_injected = False
        if all_injected:
            premium_contact.write({'state':'injected'})
    return True

#class premium_contact(models.Model):
#    _name = "premium_contact"
#     _description = u"Données personnelles de formulaires premium"
    
#    name = fields.Char('Full Name',size=100)
#    sex = fields.Selection([('Mr','Monsieur'),('Mme','Madame')],'Sexe')
#    last_name = fields.Char('Nom',size=50)
#    first_name = fields.Char('Prénom',size=50)
#    mobile = fields.Char('Mobile',size=50)
#    email = fields.Char('Email personnel',size=200)
#    birthdate = fields.Date('Date Naissance')
#    zip_code = fields.Char('Code Postal lieu résidence',size=50)
#    fb = fields.Boolean('Facebook')
#    li = fields.Boolean('LinkedIN')
#    tw = fields.Boolean('Twitter')
#    freq_fb = fields.Selection([('daily','1x/jour'),('daysbyweek','2 ou 3x/sem'),('weekly','1x/sem'),('few','- 1x/sem')],u'Fréquence Facebook')
#    freq_li = fields.Selection([('daily','1x/jour'),('daysbyweek','2 ou 3x/sem'),('weekly','1x/sem'),('few','- 1x/sem')],u'Fréquence LinkedIN')
#    freq_tw = fields.Selection([('daily','1x/jour'),('daysbyweek','2 ou 3x/sem'),('weekly','1x/sem'),('few','- 1x/sem')],u'Fréquence Twitter')
#    smartphone = fields.Boolean(u'Possède Smartphone')
#    smart_info = fields.Boolean(u'Lit infos sur SamrtPhone')
#    tablet = fields.Boolean(u'Tablette')
#    tablet_press = fields.Boolean(u'Lit infos sur tablette')
#    app_pro = fields.Boolean(u'App professionnelles')
#    invit_mail = fields.Boolean(u'Invit seulement par courriel')
#    invit_network = fields.Boolean(u'Invit seulement par R.S')
#    invit_post = fields.Boolean(u'Invitation postale')
#    sms = fields.Boolean(u'Pas de SMS')
#    ecustomer = fields.Boolean(u'eClient')
#    pay_creditcard = fields.Boolean(u'Utilise carte de crédit')
#    care_cci = fields.Boolean(u'Demande prise en charge par la CCI')
#    use_language = fields.Boolean(u'Utilise des langues étrangères')
#    eleccar = fields.Boolean(u'Voiture écolo')
#    nighter = fields.Boolean(u'Sorteur en soirée')
#    children = fields.Boolean(u'Enfants à la maison')
#    want_invest = fields.Boolean(u'Investisseur déjà ou désireux')
#    owner = fields.Boolean(u'Actionnaire ou propriétaire autres sociétés')
#    cluber = fields.Boolean(u'Participe à des Business Clubs')
#    club_cw = fields.Boolean(u'Cercle Wallonie')
#    club_cl = fields.Boolean(u'Cercle du Lac')
#    club_bni = fields.Boolean(u'BNI')
#    club_apm = fields.Boolean(u'APM')
#    club_gceq = fields.Boolean(u'Gr. C.E. du Québec')
#    club_ypowpo = fields.Boolean(u'YPO/WPO')
#    club_far = fields.Boolean(u'FAR')
#    club_fce = fields.Boolean(u'FCE')
#    club_new = fields.Boolean(u'NEW')
#    club_zoning = fields.Boolean(u'Zoning')
#    club_golf = fields.Boolean(u'Golf')
#    club_sc = fields.Boolean(u'Service Club')
#    club_other = fields.Boolean(u'Autre')
#    club_other_names = fields.Char(u'Autres - Noms',size=120)
#    networker = fields.Boolean(u'Networking')
#    freq_network = fields.Selection([('often','Plusieurs x/sem'),('weekly','1 x/sem'),('monthly','1 ou 2 x/mois'),('quaterly','1 ou 2 x/trim'),('few','2 à 3 x/an')],u'Fréquence Networking')
#    network_morning = fields.Boolean(u'Dispo networking matin')
#    network_lunch = fields.Boolean(u'Dispo networking midi')
#    network_dinner = fields.Boolean(u'Dispo networking diner')
#    network_night = fields.Boolean(u'Dispo networking soirée')
#    conf_8_10 = fields.Boolean(u'Dispo Conférence 8h-10h')
#    conf_9_11 = fields.Boolean(u'Dispo Conférence 9h-11h')
#    conf_10_12 = fields.Boolean(u'Dispo Conférence 10h-12h')
#    conf_12_14 = fields.Boolean(u'Dispo Conférence 12h-14h')
#    conf_14_16 = fields.Boolean(u'Dispo Conférence 14h-16h')
#    conf_18_20 = fields.Boolean(u'Dispo Conférence 18h-20h')
#    dispo_mon_morning = fields.Boolean(u'Dispo activ. lundi matin')
#    dispo_mon_lunch = fields.Boolean(u'Dispo activ. lundi midi')
#    dispo_mon_evening = fields.Boolean(u'Dispo activ. lundi soir')
#    dispo_tue_morning = fields.Boolean(u'Dispo activ. mardi matin')
#    dispo_tue_lunch = fields.Boolean(u'Dispo activ. mardi midi')
#    dispo_tue_evening = fields.Boolean(u'Dispo activ. mardi soir')
#    dispo_wed_morning = fields.Boolean(u'Dispo activ. mercredi matin')
#    dispo_wed_lunch = fields.Boolean(u'Dispo activ. mercredi midi')
#    dispo_wed_evening = fields.Boolean(u'Dispo activ. mercredi soir')
#    dispo_thu_morning = fields.Boolean(u'Dispo activ. jeudi matin')
#    dispo_thu_lunch = fields.Boolean(u'Dispo activ. jeudi midi')
#    dispo_thu_evening = fields.Boolean(u'Dispo activ. jeudi soir')
#    dispo_fri_morning = fields.Boolean(u'Dispo activ. vendredi matin')
#    dispo_fri_lunch = fields.Boolean(u'Dispo activ. vendredi midi')
#    dispo_fri_evening = fields.Boolean(u'Dispo activ. vendredi soir')
#    dispo_sat_morning = fields.Boolean(u'Dispo activ. samedi matin')
#    dispo_sat_lunch = fields.Boolean(u'Dispo activ. samedi midi')
#    dispo_sat_evening = fields.Boolean(u'Dispo activ. samedi soir')
#    dispo_sun_morning = fields.Boolean(u'Dispo activ. dimanche matin')
#    dispo_sun_lunch = fields.Boolean(u'Dispo activ. dimanche midi')
#    dispo_sun_evening = fields.Boolean(u'Dispo activ. dimanche soir')
#    size_25 = fields.Boolean(u'-25 personnes')
#    size_2550 = fields.Boolean(u'entre 25 et 50 personnes')
#    size_50100 = fields.Boolean(u'entre 50 et 100 personnes')
#    size_100 = fields.Boolean(u'+100 personnes')
#    price_event = fields.Selection([('all-in','All-In'),('choice','A la carte')],u'Type prix pour events')
#    interests = fields.Text('Interests/Hobbies')
#    state = fields.Selection([('draft','Draft'),('partial','Partial'),('injected','Injected')],default='draft', string='State')
#    injection_type = fields.Selection([('created','Created'),('updated','Updated'),('forced','Forced')],'Injection Type')
#    contact_id = fields.Many2one('res.partner', 'Contact')
#    injection_datetime = fields.Datetime('Injection Date')
#    premium_company_ids = fields.One2many('premium_company', 'premium_contact_id', 'Companies')
#    login = fields.Char('Login',size=40)
#    mot_passe = fields.Char('Mot de passe',size=40)
#    problems = fields.Text('Problems Injection')
#    active = fields.Boolean('Active', default=True)

#    @api.model
#    def create(self, vals):
#        if vals.has_key('birthdate') and vals['birthdate']:
#            date_items = vals['birthdate'].split('-')
#            if len(date_items) == 3:
#                if int(date_items[0]) < 1900 or int(date_items[0]) > (int(datetime.date.today().strftime('%Y'))-14):
#                    date_items[0] = 1900 + (int(date_items[0]) % 100)
#                    vals['birthdate'] = '%s-%s-%s' % (date_items[0],date_items[1],date_items[2])
#            else:
#                vals['birthdate'] = False
#        if vals.get('first_name') and vals.get('last_name'):
#            vals['last_name'] = _upper_accent(vals['last_name'])
#            vals['first_name'] = _title_accent(vals['first_name'])
#            vals['name'] =vals['last_name'] + ' ' + vals['first_name']
#            if vals.has_key('premium_companies') and vals['premium_companies']:
#                company_obj = self.env['premium_company']
#                # creation of all linked companies
#                linked_ids = []
#                for company in vals['premium_companies']:
#                    new_id = company_obj.create(company) 
#                    if new_id and new_id > 0:
#                        linked_ids.append(new_id)
#                if linked_ids:
#                    result = super(premium_contact, self).create(vals)
#                    linked_ids.write({'premium_contact_id':result.id})
#                else:
##                     result = -2
#                    raise Warning(_('Error!'),_('Please Select the  value in the field Premium Companies !'))
#            else:
#                result = super(premium_contact, self).create(vals)
#        else:
##             result = -1
#            raise Warning(_('Error!'),_('Please Enter the value of First Name and Last Name !'))
#        return result
    
#    @api.multi
#    def _try_inject_contact(self,premium_contact_id,forced_contact_id,source='automatic'):
#        error_msg = ''
#        premium_contact_obj = self.env['premium_contact']
#        contact_obj = self.env['res.partner']
#        premium_contact = premium_contact_obj.browse([premium_contact_id])[0]
#        if not premium_contact.contact_id:
#            # 1. if not forced_contact_id, we try to find a contact record from name and first_name and accept it if we can find a corresponding partner_id or mobile
#            contact_id = 0
#            if not forced_contact_id:
#                #print 'search of a valid contact linked to a good partner'
#                possible_ids = contact_obj.search([('name','=',premium_contact.last_name),('first_name','=',premium_contact.first_name)])
#                if possible_ids:
#                    # if linked premium_company already linked, we search if one of the possible contacts has a link to the partner_id of one of theses companies
#                    # if not, we search if one of these possible contacts has a link to a partner with the same vat or name
#                    valid_partner_ids = []
#                    valid_partner_vats = []
#                    valid_partner_names = []
#                    for company in premium_contact.premium_company_ids:
#                        if company.partner_id:
#                            valid_partner_ids.append(company.partner_id.id)
#                        else:
#                            if company.company_num:
#                                valid_partner_vats.append(company.company_num.upper())
#                            if company.company_name:
#                                valid_partner_names.append(_upper_accent(company.company_name))
#                    possible_contacts = contact_obj.browse(possible_ids)
#                    for contact in possible_contacts:
#                        if contact.mobile == premium_contact.mobile:
#                            contact_id = contact.id
#                        else:
#                            if contact.other_contact_ids:
#                                for partner in contact.other_contact_ids:
#                                    if partner.id in valid_partner_ids or partner.vat in valid_partner_vats or _upper_accent(partner.name) in valid_partner_names:
#                                        contact_id = partner.id
#                                        break
#                        if contact_id:
#                            break
#            else:
#                #print 'no search - forced partner'
#                contact_id = forced_contact_id
#            
#            if not contact_id:
#                if source == 'wizard':
#                    #print 'creation of contact'
#                    # creation of the contact
#                    #error_msg = 'Unable to find a contact with the same name/first_name and linked to a similar company'
#                    vals = {'name':_upper_accent(premium_contact.last_name),'first_name':_title_accent(premium_contact.first_name)}
#                    if premium_contact.email and _is_mail_personal_domain(premium_contact.email):
#                        vals['email'] = _check_email(premium_contact.email)
#                    vals = _update_contact_fields(self,premium_contact,vals)
#                    vals['premium_begin'] = datetime.date.today().strftime('%Y-%m-%d')
#                    contact_id = contact_obj.create(vals)
#                    if contact_id:
#                        if premium_contact.interests:
#                            # split interests to many 'interest' tag
#                            parameter_obj = self.env['ir.config_parameter']
#                            param_values = parameter_obj.get_param('InterestQuestionID')
#                            if param_values:
#                                INTEREST_QUESTION_ID = param_values #param_values['InterestQuestionID']
#                                answer_obj = self.pool.get('crm_profiling.answer')
#                                if '|' in premium_contact.interests:
#                                    tags = premium_contact.interests.split('|')
#                                elif ',' in premium_contact.interests:
#                                    tags = premium_contact.interests.split(',')
#                                elif ';' in premium_contact.interests:
#                                    tags = premium_contact.interests.split(';')
#                                else:
#                                    tags = [premium_contact.interests]
#                                m2m_answer_ids = []
#                                for tag in tags:
#                                    answer_id = answer_obj.create(cr,uid,{'name':'/','text':tag.strip(),'question_id':INTEREST_QUESTION_ID})
#                                    m2m_answer_ids.append( answer_id.id )
#                                contact_id.write({'answers_ids':[(6,0,m2m_answer_ids)]})
#                        premium_contact.write({'state':'partial','injection_type':'created',
#                                                   'injection_datetime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                                                   'contact_id':contact_id.id})
#            else:
#                # updating of the contact data
#                #print 'updating of contact'
#                contact = contact_id
#                vals = {'name':_upper_accent(premium_contact.last_name),'first_name':_title_accent(premium_contact.first_name)}
#                if premium_contact.email:
#                    if contact.email and contact.email <> premium_contact.email and _is_mail_personal_domain(premium_contact.email):
#                        vals['email'] = _check_email(premium_contact.email)
#                vals = _update_contact_fields(self,premium_contact,vals)
#                if not contact.premium_begin:
#                    vals['premium_begin'] = datetime.date.today().strftime('%Y-%m-%d')
#                contact.write(vals)
#                if premium_contact.interests:
#                    # split interests to many 'interest' tag
#                    parameter_obj = parameter_obj = self.env['ir.config_parameter']
#                    param_values = parameter_obj.get_param('InterestQuestionID')
#                    if param_values:
#                        INTEREST_QUESTION_ID = param_values #param_values['InterestQuestionID']
#                        answer_obj = self.env['crm_profiling.answer']
#                        if '|' in premium_contact.interests:
#                            tags = premium_contact.interests.split('|')
#                        elif ',' in premium_contact.interests:
#                            tags = premium_contact.interests.split(',')
#                        elif ';' in premium_contact.interests:
#                            tags = premium_contact.interests.split(';')
#                        else:
#                            tags = [premium_contact.interests]
#                        m2m_answer_ids = [x.id for x in contact.answers_ids if x.question_id.id != INTEREST_QUESTION_ID]
#                        for tag in tags:
#                            answer_id = answer_obj.create({'name':'/','text':tag.strip(),'question_id':INTEREST_QUESTION_ID})
#                            m2m_answer_ids.append( answer_id.id )
#                        contact.write({'answers_ids':[(6,0,m2m_answer_ids)]})
#                premium_contact.write({'state':'partial','injection_type':'updated',
#                                           'injection_datetime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                                           'contact_id':contact.id})
#            # after perhaps injecting contact data, we try to inject company data and for each of them job data
#            all_injected = True
#            premium_company_obj = self.env['premium_company']
#            job_obj = self.env['res.partner']
#            for premium_company in premium_contact.premium_company_ids:
#                final_premium_company_id = premium_company.id
#                error_msg = premium_company_obj._try_inject_company(premium_company.id,0,0,0,source)
#                if not (error_msg == 'Partner and Address Injected/Created' or error_msg == 'Partner and Address Created'):
#                    all_injected = False
#                else:
#                    # create/update job
#                    final_premium_company = premium_company_obj.browse([final_premium_company_id])[0] ## read again because the partner has perhaps been created with the _try ...
#                    #print 'premium_company.job_id'
#                    #print premium_company.job_id
#                    #print 'final_premium_company.job_id'
#                    #print final_premium_company.job_id
#                    if final_premium_company.partner_id and not final_premium_company.job_id:
#                        #print "before sentence"
#                        #print contact_id
#                        #print final_premium_company.partner_id.id
#                        sentence = """SELECT id FROM res_partner
#                                          WHERE contact_id = %s AND id in 
#                                              ( SELECT id from res_partner where parent_id = %s )""" % (str(contact.id),str(final_premium_company.partner_id.id))
#                        #print 'sentence'
#                        #print sentence
#                        res = self.env.cr.execute(sentence)
#                        #print 'res'
#                        #print res
#                        if res:
#                            #print 'updating job'
#                            # update of current job
#                            job_id = self.env['res.partner'].browse(res[0][0])
#                            #print 'job_id AAAAAA'
#                            #print job_id
#                            vals = {}
#                            vals = _update_job_fields(premium_contact,premium_company,vals)
#                            job_id.write(vals)
#                        else:
#                            if premium_company.address_work_id:
#                                right_address = premium_company.address_work_id
#                            else:
#                                right_address = premium_company.address_id
#                            if right_address:
#                                #print 'creating job inside try inject contact'
#                                # creation of job
#                                vals = {'contact_id':contact_id,'address_id':right_address.id}
#                                vals = _update_job_fields(premium_contact,premium_company,vals)
#                                job_id = job_obj.create(vals)
#                                if job_id:
#                                    premium_company.write({'job_id':job_id.id})
#                                else:
#                                    all_injected = False
#                                #print 'result job creation'
#                                #print job_id
#                            else:
#                                #print 'wait for creating job that address is created'
#                                pass
#                                #nothing to do
#            if all_injected:
#                # mark the contact as totaly injected
#                premium_contact.write({'state':'injected'})
#        else:
#            # already injected, so we just try to inject the linked companies not yet injected
#            for premium_company in premium_contact.premium_company_ids:
#                if not premium_company.state == 'injected':
#                    premium_company_obj._try_inject_company(premium_company.id,0,0,0,source)
#        return error_msg

#class premium_company(models.Model):
    
#    _name = "premium_company"
#     _description = u"Données sur les sociétés liées à un contact premium"
    
#    name = fields.Char('Name',size=250)
#    company_num = fields.Char('Company Num',size=30)
#    company_name = fields.Char('Company Name',size=200)
#    company_status = fields.Char(u'Forme juridique',size=120)
#    street = fields.Char('Street',size=200)
#    zip_city = fields.Char('Zip City',size=200)
#    zip_code = fields.Char('Zip Code',size=10)
#    zip_name = fields.Char('Zip Name',size=60)
#    phone = fields.Char('Phone',size=50)
#    fax = fields.Char('Fax',size=50)
#    employee = fields.Selection([('1','1'),('2-5','2-5'),('6-9','6-9'),('10-19','10-19'),('20-49','20-49'),('50-99','50-99'),('100-249','100-249'),('250-499','250-499'),('500+','500+')],'Employee')
#    check_formation = fields.Selection([('null',u'Ne sais pas'),('yes',u'OUI'),('no',u'Non')],'Can Use Checks Formation')
#    international = fields.Boolean('Work Internationaly')
#    prio_formation = fields.Boolean('Priority to formation')
#    invest_formation = fields.Boolean('Invest in formation')
#    zoning = fields.Boolean('In Zoning')
#    sector1 = fields.Char('Sector1',size=6)
#    sector2 = fields.Char('Sector2',size=6)
#    sector3 = fields.Char('Sector3',size=6)
#    person_statut = fields.Selection([('employee','Employee'),('independent','Independent'),('student',u'Etudiant'),('unemployed',u'En Recherche d\'emploi')],'Personal Status')
#    inde_statut = fields.Selection([('physical',u'Personne Physique'),('manager','Dirigeant d\'entreprise'),('management','Société de management'),('professional','Profession libérale')],'Independent Statut')
#    main_dir = fields.Boolean(u'Poste au sein de la direction générale')
#    main_dir_type = fields.Selection([('onlydir',u'Patron propriétaire'),('majority','Patron majoritaire'),('associated',u'Patron associé'),('number1','Numéro 1')],u'Direction générale')
#    main_dir_arrival = fields.Selection([('creator',u'Créé son entreprise'),('laterparticiper',u'Acquis des patrs en cours de route'),('buyer',u'Repris une entreprise')],u'Patron qui a')
#    main_dir_year =  fields.Char(u'Année arrivée',size=4)
#    buy_from = fields.Selection([('family',u'Membre de la famille'),('boss',u'Ancien patron'),('company',u'Tiers')],'Acquise auprès de')
#    shareholder = fields.Selection([('2','2'),('3','3'),('4','4'),('5+','5 et +'),('stock_exchange',u'Société cotée en Bourse')],'Nbre actionnaires')
#    invest = fields.Boolean(u'Présence Invest')
#    investor = fields.Boolean(u'Présence investisseur ou Business Angel')
#    crowdfund = fields.Boolean(u'Crowdfunding')
#    family = fields.Boolean(u'Membres de la famille')
#    steering = fields.Boolean(u'Membre du comité de direction')
#    decision_level = fields.Selection([('direction',u'Direction'),('cadre',u'Cadre'),('employee',u'Employé')],u'Niveau de décision')
#    purchase = fields.Boolean(u'Dépt. Achats')
#    administration = fields.Boolean(u'Dépt. Administration')
#    commercial = fields.Boolean(u'Dépt. Commercial')
#    communication = fields.Boolean(u'Dépt. Communication')
#    public_relation = fields.Boolean(u'Dépt. Relations publiques')
#    energy = fields.Boolean(u'Dépt. Energie et Environ')
#    export = fields.Boolean(u'Dépt. Export')
#    finance = fields.Boolean(u'Dépt. Finances')
#    it = fields.Boolean(u'Dépt. IT')
#    logistic = fields.Boolean(u'Dépt. Logistic')
#    marketing = fields.Boolean(u'Dépt. Marketing')
#    operations = fields.Boolean(u'Dépt. Opérations')
#    production = fields.Boolean(u'Dépt. Production')
#    projects = fields.Boolean(u'Dépt. Projets')
#    r_d = fields.Boolean(u'Dépt. R&D')
#    hr = fields.Boolean(u'Dépt. RH')
#    secretary = fields.Boolean(u'Dépt. Secrétariat')
#    security = fields.Boolean(u'Dépt. Sécurité')
#    technical = fields.Boolean(u'Dépt. Technique')
#    web = fields.Boolean(u'Dépt. Web')
#    others = fields.Boolean(u'Dépt. Autres')
#    others_name = fields.Char(u'Autre département',size=50)
#    title = fields.Char('Full Title',size=1000)
#    importance = fields.Integer('Sequence')
#    job_id = fields.Many2one('res.partner','Fonction')
#    address_id = fields.Many2one('res.partner','Address')
#    address_work_id = fields.Many2one('res.partner','Working address')
#    partner_id = fields.Many2one('res.partner','Partner')
#    state = fields.Selection([('draft','Draft'),('injected','Injected')],default='draft' , string='State')
#    injection_type = fields.Selection([('created','Created'),('updated','Updated'),('forced','Forced')],'Injection Type')
#    injection_datetime = fields.Datetime('Injection Date')
#    premium_contact_id = fields.Many2one('premium_contact','Premium Contact')
#    activity_description = fields.Text('Activity Description')
#    equal_representation = fields.Char('Equal Representation',size=10)
#    street_work = fields.Char('Street',size=200)
#    zip_code_work = fields.Char('Zip Code',size=10)
#    zip_name_work = fields.Char('Zip Name',size=60)
#    problems = fields.Text('Problems Injection')
#    active = fields.Boolean('Active', default=True)

#    @api.model
#    def _valid_company_num(self,company_num):
#        '''
#        Check the VAT number depending of the country.
#        http://sima-pc.com/nif.php
#        '''
#        vat_country, vat_number = company_num[:2].lower(), company_num[2:].replace(' ', '')
#        partner_obj = self.env['res.partner']
#        check = getattr(partner_obj, 'check_vat_' + vat_country)
#        if not check(vat_number):
#            return False
#        return True
    
#    @api.model
#    def create(self, vals):
#        if vals.get('company_name',False)  and vals.get('company_num',False):
#            vals['company_name'] = _upper_accent(vals['company_name'])
#            vals['company_num'] = _upper_accent(vals['company_num'])
#            if self._valid_company_num(vals['company_num']):
#                vals['name'] = u'%s [%s]' % (vals['company_name'],vals['company_num'])
#                if vals.get('zip_city',False):
#                    vals['zip_city'] = _upper_accent(vals['zip_city']).strip()
#                    vals['name'] += ' - ' + vals['zip_city']
#                # validation of phone or fax not here but during the injection in res.partner.... so we keep what the user encoded here
#                # We validate the activity sectors, also during the injection to res.partner.address to keep an image of the values encoded by the user
#                result = super(premium_company, self).create(vals)
#            else:
#                raise Warning(_('Error!'),_('Not Valid Company Num !'))
#        else:
##             result = -1
#            raise Warning(_('Error!'),_('Please fill the value for fields Company Name and Company Num !'))
#        return result
#    
#    @api.multi
#    def _try_inject_company(self,premium_company_id,forced_partner_id,forced_address_id,forced_address_work_id,source='automatic'):
#        error_msg = ''
#        company_obj = self.env['premium_company']
#        partner_obj = self.env['res.partner']
#        premium_company = company_obj.browse(premium_company_id)[0]
#        # 1. if not forced_partner_id, we try to find a partner record from company_num OR (a partner with the same name AND ( a contact with the same name, the same mobile ))
#        partner_id = 0
#        address_id = 0
#        if not forced_partner_id:
#            #print 'search of a valid partner with the same vat'
#            partner_ids = partner_obj.search([('vat','=',_upper_accent(premium_company.company_num))])
#            if partner_ids and len(partner_ids) == 1:
#                partner_id = partner_ids[0]
#        else:
#            #print 'no search - forced partner'
#            partner_id = forced_partner_id
#        if not partner_id:
#            # we try to find a partner with the same name AND with a contact with ( the same contact_id XOR ( (the same first and last names ) OR same mobile  )
##             partner_ids = partner_obj.search([('name','=',_clean_api(_upper_accent(premium_company.company_name)))])
#            possible_partners = partner_obj.search([('name','=',_clean_api(_upper_accent(premium_company.company_name)))]) #partner_obj.browse(cr,uid,partner_ids)
#            if premium_company.premium_contact_id and premium_company.premium_contact_id.contact_id:
#                forced_contact_id = premium_company.premium_contact_id.contact_id.id
#            else:
#                forced_contact_id = 0
#            for partner in possible_partners:
#                if partner.child_ids:
#                    for addr in partner.child_ids:
#                        if addr.other_contact_ids:
#                            for job in addr.other_contact_ids:
#                                if job.contact_id:
#                                    if forced_contact_id:
#                                        if job.contact_id.id == forced_contact_id:
#                                            partner_id = partner.id
#                                            #print 'inside 1'
#                                            #address_id = addr.id # to force a new search later
#                                            break
#                                    elif ( _upper_accent(job.contact_id.name) == _upper_accent(premium_company.premium_contact_id.last_name) and \
#                                         _title_accent(job.contact_id.first_name) == _title_accent(premium_company.premium_contact_id.first_name) ) or \
#                                         ( job.contact_id.mobile == _check_phone_num(premium_company.premium_contact.mobile) ):
#                                        partner_id = partner.id
#                                        #print 'inside 2'
#                                        #address_id = addr.id # to force a new search later
#                                        break
#                            if partner_id:
#                                break
#                    if partner_id:
#                        break
#            if partner_id:
#                #print 'we have found a partner from name and contact names - it s a miracle'
#                pass
#        address_id = 0
#        address_work_id = 0
#        if not partner_id:
#            error_msg = 'Unable to find a partner with the same company number; OR with the same name (with a corresponding contact)'
#        else:
#            # 2. If partner_id and no address_id, we try to find an similar address (same street and zip code) OR an address with a contact with the same name
#            if not forced_address_id:
#                #print 'search address'
#                partner = partner_obj.browse([partner_id])[0]
#                if partner.child_ids:
#                    for addr in partner.child_ids:
#                        if _upper_accent(addr.street) == _upper_accent(premium_company.street) or (premium_company.street_work and (_upper_accent(addr.street) == _upper_accent(premium_company.street_work))): ## TODO ZIP CODE
#                            #print 'address_id inside'
#                            address_id = addr.id
#                            break
#                        else:
#                            if addr.other_contact_ids and not premium_company.street_work: ## If street_work, we don't search for an address with a contact with the same name
#                                print 'inside 3'
#                                for job in addr.other_contact_ids:
#                                    print _upper_accent(job.contact_id.name) + ' =? ' + _upper_accent(premium_company.premium_contact_id.last_name)
#                                    if job.contact_id and _upper_accent(job.contact_id.name) == _upper_accent(premium_company.premium_contact_id.last_name) and \
#                                         _title_accent(job.contact_id.first_name) == _title_accent(premium_company.premium_contact_id.first_name):
#                                        address_id = addr.id
#                                        break
#                                if address_id:
#                                    break
#            else:
#                #print 'forced_address_id 1'
#                address_id = forced_address_id
#            if not forced_address_work_id and premium_company.street_work:
#                #print 'search working address'
#                partner = partner_obj.browse([partner_id])[0]
#                if partner.child_ids:
#                    for addr in partner.child_ids:
#                        if _upper_accent(addr.street) == _upper_accent(premium_company.street_work): ## TODO ZIP CODE
#                            address_work_id = addr.id
#                            break
#                        else:
#                            if addr.other_contact_ids:
#                                for job in addr.other_contact_ids:
#                                    print _upper_accent(job.contact_id.name) + ' =? ' + _upper_accent(premium_company.premium_contact_id.last_name)
#                                    if job.contact_id and _upper_accent(job.contact_id.name) == _upper_accent(premium_company.premium_contact_id.last_name) and \
#                                         _title_accent(job.contact_id.first_name) == _title_accent(premium_company.premium_contact_id.first_name):
#                                        address_work_id = addr.id
#                                        break
#                                if address_work_id:
#                                    break
#            else:
#                address_work_id = forced_address_work_id
#        #print 'actual result'
#        #print partner_id
#        #print address_id
#        #print address_work_id
#        #print source
#        # 3a. If no partner_id and no address_id AND source = 'wizard', we create a new partner, and a new address
#        if not partner_id and not address_id and not address_work_id and source == 'wizard':
#            #print 'Wizard without partner and address => creation of new records'
#            partner_id = _create_new_partner(self,premium_company)
#            #print 'partner_id'
#            #print partner_id
#            if partner_id:
#                premium_company.write({'partner_id':partner_id})
##                 premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#                #print 'inside 1'
#                #print premium_company.partner_id
#                address_id = _create_new_address_classic(self,premium_company)
#                if premium_company.street_work:
#                    address_work_id = _create_new_address_work(self,premium_company)
#                if address_id and (address_work_id or not premium_company.street_work):
#                    error_msg = 'Partner and Address Created'
#                    premium_company.write({'address_id':address_id,'address_work_id':address_work_id})
##                     premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#                    if premium_company.premium_contact_id and premium_company.premium_contact_id.contact_id:
#                        premium_contact = premium_company.premium_contact_id
#                        #print 'inside try inject company inject job 1'
#                        job_id = _inject_job(self,premium_company,premium_contact)
#                        if job_id:
#                            premium_company.write({'job_id':job_id,'state':'injected',
#                                                   'injection_type': forced_partner_id and 'forced' or 'created',
#                                                   'injection_datetime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
#                            _mark_as_injected(self,premium_contact)
#                        #print 'result'
#                        #print job_id
#        # 3b. If partner_id and no address_id, we create a new address
#        elif partner_id and not (address_id and (address_work_id or not premium_company.street_work)):
#            premium_company.write({'partner_id':partner_id})
##             premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#            #print 'Wizard with partner but without address => creation of new record of address'
#            #print premium_company.partner_id
#            _update_partner(self,premium_company)
#            #print 'inside 2 part 1'
#            #print 'id des deux addresses'
#            #print address_id
#            #print address_work_id
#            #print premium_company.address_id
#            #print premium_company.address_work_id
#            #
#            if address_id and address_id > 0:
#                premium_company.write({'address_id':address_id})
##                 premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#                _update_address(self,premium_company)
##                 premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#            else:
#                address_id = _create_new_address_classic(self,premium_company)
#            if premium_company.street_work:
#                #print 'wizard part 2 - address_work_id '
#                #print address_work_id
#                if address_work_id and address_work_id > 0:
#                    #print address_work_id
#                    premium_company.write({'address_work_id':address_work_id})
##                     premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#                    #print 'wizard part 2 2 '
#                    #print premium_company.address_work_id
#                    _update_working_address(self,premium_company)
##                     premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#                else:
#                    address_work_id = _create_new_address_work(self,premium_company)
#            if address_id and (address_work_id or not premium_company.street_work):
#                error_msg = 'Partner and Address Injected/Created'
#                premium_company.write({'address_id':address_id,'address_work_id':address_work_id})
##                 premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#                if premium_company.premium_contact_id and premium_company.premium_contact_id.contact_id:
#                    premium_contact = premium_company.premium_contact_id
#                    #print 'inside try inject company 2 inject job'
#                    job_id = _inject_job(self,premium_company,premium_contact)
#                    if job_id:
#                        premium_company.write({'job_id':job_id,'state':'injected',
#                                               'injection_type': forced_partner_id and 'forced' or 'updated',
#                                               'injection_datetime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
#                        _mark_as_injected(self,premium_contact)
#                    #print 'result'
#                    #print job_id
#        # 3c. If partner_id and address_id, we inject the data, we mark the record as 'injected' AND if the source is 'wizard', we try to also inject the linked premium_contact
#        elif partner_id and address_id and (address_work_id or not premium_company.street_work):
#            #print 'Wizard with partner and address => updating of patrner and address records'
#            premium_company.write({'partner_id':partner_id,'address_id':address_id,'address_work_id':address_work_id})
##             premium_company = company_obj.browse(cr,uid,[premium_company_id])[0]
#            _update_partner(self,premium_company)
#            _update_address(self,premium_company)
#            if address_work_id:
#                _update_working_address(self,premium_company)
#            error_msg = 'Partner and Address Injected'
#            if premium_company.premium_contact_id and premium_company.premium_contact_id.contact_id:
#                premium_contact = premium_company.premium_contact_id
#                #print 'inside try inject company3 inject job'
#                job_id = _inject_job(self,premium_company,premium_contact)
#                if job_id:
#                    premium_company.write({'job_id':job_id,'state':'injected',
#                                           'injection_type': forced_partner_id and 'forced' or 'updated',
#                                           'injection_datetime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
#                    _mark_as_injected(self,premium_contact)
#                #print 'result'
#                #print job_id
#        #print 'error_msg'
#        #print error_msg
#        return error_msg

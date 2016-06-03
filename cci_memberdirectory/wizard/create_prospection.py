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

import datetime
from openerp import models, fields, api, _

def _check_digit_1_digit(digital_string):
    digit_sum = 0
    for carac in digital_string:
        if carac.isdigit():
            digit_sum += int(carac)
    return str(digit_sum)[-1:]

def _link_id(record_id):
    partner = str(record_id).rjust(5, '0')
    inv_partner = ''
    for carac in partner:
        inv_partner = carac + inv_partner
    year = (7 * int(inv_partner[3:4])) + int(inv_partner[2:3]) + 13  # # year was the last two caracters of the current year
    link_id = inv_partner[0:3] + str(year) + inv_partner[3:4]
    link_id += _check_digit_1_digit(link_id)
    link_id += inv_partner[4:5]
    rest = int(link_id) % 93
    link_id += _check_digit_1_digit(link_id)
    link_id = link_id + str(rest).rjust(2, '0')
    return link_id    

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

class cci_memberdirectory_create_prospection(models.TransientModel):
    _name = 'cci.memberdirectory.create.prospection'
    
    new1 = fields.Boolean('New')
    raz_exclude = fields.Boolean('Set All dir_exclude to false')
    
    def get_phone_country_prefix(self):
        result = []
        obj_country = self.env['cci.country']
        country_ids = obj_country.search([('phoneprefix', '!=', False), ('phoneprefix', '!=', 0)])
        if country_ids:
            countries = country_ids.read(['phoneprefix'])
            result = [str(x['phoneprefix']) for x in countries]
        return result
     
    @api.multi
    def create_prospection_list(self):
        # def get_activity_sectors(partner,oldcateg_ids,dOldSectID2NewID):
        #    secteurs = [False,False,False]
        #    current_secteur = 0
        #    if partner.category_id:
        #        for oldcateg in partner.category_id: ## category_id is, not like his name define, an array of category ids
        #            if (oldcateg.id in oldcateg_ids) and (oldcateg.id not in secteurs) and dOldSectID2NewID.has_key(oldcateg.id):
        #                secteurs[current_secteur] = dOldSectID2NewID[oldcateg.id]
        #                current_secteur += 1
        #                if current_secteur > 2:
        #                    break
        #    return secteurs
        addr_proxy_obj = self.env['directory.address.proxy']
        cont_proxy_obj = self.env['directory.job.proxy']
        # extract the ID of the website
        obj_user = self.env['res.users']
        website_id = obj_user.search([('name', '=', 'Noomia')], limit=1)
        #
        modifiable_proxy_ids = []
        if self.new1:
            # job2delete_ids = job2delete_proxy_obj.search(cr,uid,[])
            # job2delete_proxy_obj.unlink(cr,uid,job2delete_ids)
            # sector_ids = sector_proxy_obj.search(cr,uid,[])
            # sector_proxy_obj.unlink(cr,uid,sector_ids)
            cont_ids = cont_proxy_obj.search([])
            cont_ids.write({'active': False})
            addr_ids = addr_proxy_obj.search([])
            addr_ids.write({'active': False})
            used_res_partner_address_ids = []
        else:
            existing_addr_ids = addr_proxy_obj.search([])
            existing_addresses = existing_addr_ids.read(['address_id', 'write_uid', 'user_validated', 'internal_validated'])
            used_res_partner_address_ids = [x['address_id'][0] for x in existing_addresses]
            # WRITE_UID IS DEFINED SO CAN BE USED IN SEARCHS
            # sentence = """SELECT id FROM directory_address_proxy
            #                        WHERE address_id in (%s) AND write_uid <> %s AND NOT user_validated and NOT internal_validated""" % (','.join([str(x) for x in used_res_partner_address_ids]),str(website_id))
            # cr.execute(sentence)
            # res = cr.fetchall()
            # modifiable_proxy_ids = [x[0] for x in res]
            modifiable_proxy_ids = [x['id'] for x in existing_addresses if not x['write_uid'] or (x['write_uid'] and x['write_uid'][0] <> website_id and not x['user_validated'] and not x['internal_validated'])]
        # extract all ids of activity sector categories and remove '[303]' from name
        obj_categ = self.env['res.partner.activsector']
        categ_ids = obj_categ.search([])
        # old_len = 0
        # categ_ids = [ data['form']['sector'] ]
        # while len(categ_ids) > old_len:
        #    new_ids = categ_ids[old_len:] # ids of categories added last time
        #    old_len = len(categ_ids) # the new frontier ...
        #    new_categs = obj_categ.read(cr,uid,new_ids,['child_ids'])
        #    for categ in new_categs:
        #        if categ['child_ids']:
        #            categ_ids.extend(categ['child_ids'])
        categs = categ_ids.read(['code'])
        dCategs = {}
        dSectCode2ID = {}
        # dCategID2DirSectorID = {}
        for categ in categs:
            dCategs[categ['id']] = categ['code']
            dSectCode2ID[categ['code']] = categ['id']
        # table for converting old activity sectors to new ones
        dOldSectID2NewID = {}
        parameter_obj = self.env['ir.config_parameter']
        param_values = parameter_obj.get_param('ActivityCodeRootID')
        if param_values:
            activityCodeRootID = param_values
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
        member_wo_address = 0
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
        subscriptions = subscription_obj.search([('type_id', 'in', sub_type_ids), ('state', '=', 'current')])
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
                for possible_job in subs.contact_id.other_contact_ids:
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
        partners = partner_obj.browse(partner_ids)
        for partner in partners:
            if partner.child_ids:
                partner_no_email = ''
                for addr in partner.child_ids:
                    if addr.dir_exclude and data['form']['raz_exclude']:
                        correction = {'dir_exclude':False}
                        addr.write(correction)
                        not_in_directory_count += 1
                    # TODO REPLACE BY A CALL TO CLASS METHOD
                    (errors, res_addr_count, res_modif_count, res_email_count, res_cont_count) = addr_proxy_obj._synchro_address(addr, partner, modifiable_proxy_ids, full_page_partner_ids, self.new1, website_id, dCategs, dSectCode2ID, dOldSectID2NewID, oldcateg_ids)
                    if errors:
                        partner_no_email = '\n-----------------------------\nPartenaire : %s [%s] %s' % (partner.name, partner.id, errors)
                        partners_wo_emails += partner_no_email
                    addr_count += res_addr_count
                    modif_count += res_modif_count
                    email_count += res_email_count
                    cont_count += res_cont_count
 
            else:
                member_wo_address += 1
        results = 'Selected Partners : %s\nPublished Addresses : %s\nDirectory Exclude cleaned : %s\nContacts found : %s\nEmail Count : %s\nMembers without addresses : %s' % (str(len(partner_ids)),
                                                                                                                                               str(addr_count),
                                                                                                                                               str(not_in_directory_count),
                                                                                                                                               str(cont_count),
                                                                                                                                               str(email_count),
                                                                                                                                               str(member_wo_address))
        ctx = self.env.context.copy()
        ctx.update({'results': results, 'no_email': partners_wo_emails})
        view = self.env.ref('cci_memberdirectory.view_cci_memberdirectory_create_prospection_final')
        
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.memberdirectory.create.prospection.final',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_memberdirectory_create_prospection_final(models.TransientModel):
    _name = 'cci.memberdirectory.create.prospection.final'
    
    results = fields.Text('Results', readonly=True)
    no_email = fields.Text('Partners w/o email', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_memberdirectory_create_prospection_final, self).default_get(fields)
        if self.env.context.get('results'):
            rec['results'] = self.env.context['results']
        if self.env.context.get('no_email'):
            rec['no_email'] = self.env.context['no_email']
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
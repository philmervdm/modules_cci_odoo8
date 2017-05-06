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
import datetime
import logging
from xlwt import *
import re
from itertools import groupby
from operator import itemgetter

from openerp import models, fields, api, _
from openerp.osv.expression import get_unaccent_wrapper
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)

BELGIAN_PHONE_PREFIX = ['0456','0460','04660','04661','04662','04681','04682','04683','0470', '0471', '0472', '0473', '0474', '0475', '0476', '0477', '0478', '0479', '0483','0484', '0485', '0486', '0487', '0488', '0489','0490','0491', '0492', '0493', '0494', '0495', '0496', '0497', '0498', '0499']

def group(lst, col):
    return dict((k, [v for v in itr]) for k, itr in groupby(sorted(lst, key=lambda x: x[col]), itemgetter(col)))

class res_company(models.Model):
    _inherit = 'res.company'
    _description = 'res.company'

    def _get_default_ad(self, addresses):
        city = post_code = address = country_code = ''
        for ads in addresses:
            if ads.type == 'default':
                if ads.zip_id:
                    city = ads.zip_id.city
                    post_code = ads.zip_id.name
                if ads.street:
                    address = ads.street
                if ads.street2:
                    address += ads.street2
                if ads.country_id:
                    country_code = ads.country_id.code
        return city, post_code, address, country_code

    federation_key = fields.Char('ID for the Federation', size=50, help="ID key for the sending of data to the belgian CCI's Federation")

class res_partner_reason(models.Model):
    _name = 'res.partner.reason'
    _description = 'res.partner.reason'
    
    name = fields.Char('Reason', size=50, required=True, index=True)

#class res_partner_state2(models.Model):
#    _name = 'res.partner.state2'
#    _description = 'res.partner.state2'
#
#    name = fields.Char('Customer Status', size=50, required=True)

class res_partner_article_review(models.Model):
    _name = 'res.partner.article.review'
    _description = 'res.partner.article.review'

    name = fields.Char('Name', size=50, required=True)
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    article_ids = fields.One2many('res.partner.article', 'review_id', string='Articles')

class res_partner_article(models.Model):
    _name = 'res.partner.article'
    _description = 'res.partner.article'
    _rec_name = 'article_id'
    
    article_id = fields.Char('Article', size=256, default=lambda self: self.env['ir.sequence'].get('res.partner.article'))
    page = fields.Integer('Page', size=16)
    article_length = fields.Float('Length')
    picture = fields.Boolean('Picture')
    data = fields.Boolean('Data')
    graph = fields.Boolean('Graph')
    summary = fields.Text('Summary')
    source_id = fields.Char('Source', size=256)
    date = fields.Date('Date', required=True)
    title = fields.Char('Title', size=250, required=True)
    subtitle = fields.Text('Subtitle')
    press_review = fields.Boolean('In the next press review', help='Must be inserted on the next press review')
    canal_id = fields.Char('Reference', size=200, help='A text with or without a link incorporated')
    review_id = fields.Many2one('res.partner.article.review', 'Review')
    partner_ids = fields.Many2many('res.partner', 'res_partner_article_rel', 'article_id', 'partner_id', string='Partners', domain=[('is_company', '=', True)])
    contact_ids = fields.Many2many('res.partner', 'res_partner_contact_article_rel', 'article_id', 'contact_id', string='Contacts', domain=[('is_company', '!=', True)])

class res_partner_article_keywords(models.Model):
    _name = 'res.partner.article.keywords'
    _description = 'res.partner.article.keywords'
    
    name = fields.Char('Name', size=80, required=True)
    article_ids = fields.Many2many('res.partner.article', 'partner_article_keword_rel', 'keyword_id', 'article_id', string='Articles')

class res_partner_article(models.Model):
    _inherit = 'res.partner.article'

    keywords_ids = fields.Many2many('res.partner.article.keywords', 'article_keyword_rel', 'article_id', 'keyword_id', string='Keywords')

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'res.partner'
     
    #def _commercial_fields(self, cr, uid, context=None):
    #    """ Returns the list of fields that are managed by the commercial entity
    #    to which a partner belongs. These fields are meant to be hidden on
    #    partners that aren't `commercial entities` themselves, and will be
    #    delegated to the parent `commercial entity`. The list is meant to be
    #    extended by inheriting classes. """
    #    return ['vat', 'credit_limit','membership_state']

    @api.model
    def strip_accents(self,text):
        """
        Strip accents from input String.

        :param text: The input string.
        :type text: String.

        :returns: The processed String.
        :rtype: String.
        """
        import unicodedata
        try:
            text = unicode(text, 'utf-8')
        except NameError: # unicode is a default on python 3 
            pass
        except TypeError: # if text is already unicode
            pass
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        return str(text)

    @api.model
    def only_digits(self,text):
        result = ''
        for caracter in text:
            if caracter.isdigit():
                result += caracter
        return result
        
    @api.model
    def unformat_phonenr(self,text):
        """
        Convert a full phone number to a 'only_digit' number. Example : "04/123.45.67" => ["041234567",""]
        Sometimes, a number can be completed by a description between parenthesis. Example : "04/123.45.67 (office 125)" => ["041234567","office 125"]

        :param text: The input string.
        :type text: String.

        :returns: The processed String and the possible extra string between parenthesis
        :rtype: [String,String]
        """
        number = u''
        extra = u''
        text = text.strip()
        if text[0] == u'+':
            text = '00'+text[1:]
        if u'(' in text:
            base_string = text.strip()
            extra_begin = base_string.find(u'(')
            extra_end = base_string.find(u')')
            base_number = base_string[0:extra_begin-1]
            extra = base_string[extra_begin:extra_end+1].strip()
        else:
            base_number = text
        number = self.only_digits(base_number)
        return [number,extra]

    @api.model
    def check_phonenr(self,cleaned_phonenr):
        """
        Check if a phone number is correct
        If international or empty, considered good

        :param text: A cleaned Phone number. Cleaned = without separators and without complement of information at right between parenthesis
        :type text: String.

        :returns: True if correct, False else
                  The string is the cleaned phone number if correct, error message if not
        :rtype: [Boolean,String]
        """
        if not cleaned_phonenr:
            return [True,'']
        result = [True,cleaned_phonenr]
        if not cleaned_phonenr.startswith('00'):
            is_gsm = False
            for item in BELGIAN_PHONE_PREFIX:
                is_gsm = cleaned_phonenr.startswith(item)
                if is_gsm:
                    break
            if is_gsm:
                if not len(cleaned_phonenr) == 10:
                    result = [False,_(u'Invalid GSM Phone number (%s). Only 10 figures numbers are allowed.') % cleaned_phonenr]
            else:
                if not len(cleaned_phonenr) == 9:
                    result = [False, _(u'Invalid Fix Phone number (%s). Only 9 figures numbers are allowed.') % cleaned_phonenr]
        return result

    @api.model
    def format_phonenr(self,text):
        """
        Strip accents from input String.

        :param text: The input string.
        :type text: String.

        :returns: The processed String
        :rtype: String
        """
        (base_number,extra) = self.unformat_phonenr(text)
        (correct_phonenr,nr_or_error_msg) = self.check_phonenr(base_number)
        result = u''
        if correct_phonenr:
            phonenr = nr_or_error_msg
            if phonenr[0:2] == u'00':
                ### international number : we check the prefix to detect its length then we format the rest with xx.xx.xx .... and we keep the '00 prefix' notation (not + prefix)
                intl_prefix = ''
                countries = self.env['cci.country'].search([('phoneprefix','>',0)])
                for country in countries:
                    if phonenr[2:2+len(str(country.phoneprefix))] == str(country.phoneprefix):
                        intl_prefix = str(country.phoneprefix)
                        break
                if not intl_prefix:
                    intl_prefix = phonenr[2:4]
                result = phonenr[0:2+len(intl_prefix)]+' '
                if len(phonenr) > (2+len(intl_prefix)):
                    chunks = re.findall('.{1,2}', phonenr[2+len(intl_prefix):] )
                    result += '.'.join(chunks)
            else:
                gsm_prefix = ''
                for item in BELGIAN_PHONE_PREFIX:
                    if phonenr.startswith(item):
                        gsm_prefix = item
                        break
                if gsm_prefix:
                    result = u'%s/%s.%s.%s' % (phonenr[0:4],phonenr[4:6],phonenr[6:8],phonenr[8:10])
                else:
                    if phonenr[0:2] in [u'02',u'03',u'04',u'09']:
                        result = u'%s/%s.%s.%s' % (phonenr[0:2],phonenr[2:5],phonenr[5:7],phonenr[7:9])
                    else:
                        result = u'%s/%s.%s.%s' % (phonenr[0:3],phonenr[3:5],phonenr[5:7],phonenr[7:9])
            if extra:
                result += (u' %s' % extra)
        return result

    @api.model
    def email_correct(self,addr):
        """
        Check if email is correctly formatted. The address must be in lowercase OR uppercase mixed and without leading or trailing spaces

        :param addr: email address to check
        :type text: String.

        :returns: Correct or not
        :rtype: Boolean
        """
        res_match = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$)", addr)
        return (res_match != None)
    
    @api.model
    def create(self, vals):
        if vals.has_key('vat') and vals['vat']:
            vals.update({'vat':vals['vat'].upper()})
        if vals.has_key('lastname'):
            vals['lastname'] = self.strip_accents(vals['lastname']).upper().strip()
        if vals.has_key('firstname'):
            vals['firstname'] = vals['firstname'].title().strip()
        if vals.has_key('phone'):
            vals['phone'] = self.format_phonenr(vals['phone'])
        if vals.has_key('mobile'):
            vals['mobile'] = self.format_phonenr(vals['mobile'])
        if vals.has_key('fax'):
            vals['fax'] = self.format_phonenr(vals['fax'])
        if vals.has_key('email'):
            vals['email'] = vals['email'].strip().lower().replace ('\n','').replace('\r','')
        if vals.has_key('type') and vals['type'] == 'contact' and (vals.has_key('lastname') or vals.has_key('firstname')):
            vals.update({'name':((vals.has_key('lastname') and vals['lastname'] or '') + ' ' + (vals.has_key('firstname') and vals['firstname'] or '')).strip()})
        new_id = super(res_partner, self).create(vals)
        # complete the user_id (salesman) automatically according to the zip code of the main address. Use res.partner.zip to select salesman according to zip code
        if vals.has_key('child_ids') and vals['child_ids']:
            for add in vals['child_ids']:
                if add[2]['zip_id'] and add[2]['type'] == 'default':
                    data = self.env['res.partner.zip'].browse(add[2]['zip_id'])
                    saleman_id = data.user_id.id
                    new_id.write({'user_id': saleman_id})
        return new_id
     
    @api.multi
    def write(self, vals):
        partner_obj = self.env['res.partner']
        list = []
        if vals.has_key('vat') and vals['vat']:
            vals.update({'vat': vals['vat'].upper()})
        if vals.has_key('lastname'):
            vals['lastname'] = partner_obj.strip_accents(vals['lastname']).upper().strip()
        if vals.has_key('firstname'):
            vals['firstname'] = vals['firstname'].title().strip()
        current_type = vals.get('type',self.type or '').strip()
        current_lastname = vals.get('lastname',self.lastname or '')
        if not current_lastname:
            current_lastname = ''
        current_firstname = vals.get('firstname',self.firstname or '')
        if not current_firstname:
            current_firstname = ''
        if current_type == 'contact' and (vals.has_key('lastname') or vals.has_key('firstname')):
            vals.update({'name':(current_lastname + ' ' + current_firstname).strip()})
        if vals.has_key('function_ids'):
            new_function_codes = ''
            new_functions = self.env['res.partner.function'].browse(vals['function_ids'][0][2])
            for new_function in new_functions:
                new_function_codes += new_function.code.strip() + ','
            vals.update({'function_codes':new_function_codes})
        if vals.has_key('phone'):
            vals['phone'] = self.format_phonenr(vals['phone'])
        if vals.has_key('mobile'):
            vals['mobile'] = self.format_phonenr(vals['mobile'])
        if vals.has_key('fax'):
            vals['fax'] = self.format_phonenr(vals['fax'])
        if vals.has_key('email'):
            vals['email'] = vals['email'].strip().lower().replace ('\n','').replace('\r','')
        for partner in self:
            if not partner.user_id:
                # if not self.pool.get('res.partner').browse(cr, uid, ids)[0].user_id.id:
                if 'child_ids' in vals:
                    for add in vals['child_ids']:
                        addr = partner_obj.browse(add[1])
                        if addr.zip_id and addr.type == 'default':
                            saleman_id = addr.zip_id.user_id.id
                            if saleman_id:
                                ctx = self.env.context.copy()
                                if ctx and ('__last_update' in ctx):
                                    del ctx['__last_update']
                                partner.with_context(ctx).write({'user_id': saleman_id})
        return super(res_partner, self).write(vals)
#    @api.multi
#    def write(self, vals):
#        #unaccent = get_unaccent_wrapper(env.cr)
#        if vals.has_key('lastname'):
#            #vals['lastname'] = unaccent(vals['lastname']).upper().strip()
#            vals['lastname'] = vals['lastname'].upper().strip()
#        if vals.has_key('firstname'):
#            vals['firstname'] = vals['firstname'].title().strip()
#        current_type = vals.get('type',self.type or '').strip()
#        current_lastname = vals.get('lastname',self.lastname or '')
#        if not current_lastname:
#            current_lastname = ''
#        current_firstname = vals.get('firstname',self.firstname or '')
#        if not current_firstname:
#            current_lastname = ''
#        if current_type == 'contact' and (vals.has_key('lastname') or vals.has_key('firstname')):
#            vals.update({'name':(current_lastname + ' ' + current_firstname).strip()})
#        super(res_partner, self).write(vals)
#        return True

    @api.constrains('email')
    def check_email(self):
        # constraints to ensure that the email addrss is correct (ionce stripped and lowercased
        if self.email:
            if not self.email_correct(self.email.strip().lower()):
                raise Warning (_('Warning'), _('Email address seems incorrect !'))
        return True
     
    @api.constrains('child_ids')
    def check_address(self):
        # constraints to ensure that there is only one default address by partner.
        list = []
        for add in self.child_ids:
            if add.type in list and add.type == 'default':
                raise Warning (_('Warning'), _('Only One default address is allowed!'))
            list.append(add.type)
        return True
     
    @api.constrains('activity_code_ids')
    def _check_activity(self):
        for data in self:
            list_activities = []
            cnt = 0
            for activity in data.activity_code_ids:
                if activity.importance == 'main':
                    cnt += 1
                    if cnt > 1:
                        raise Warning (_('Warning'), _('Partner Should have only one Main Activity!'))
        return True
     
    @api.multi
    def onchange_lfname(self, lastname, firstname):
        value = {'name':((lastname or '') + ' ' + (firstname or '')).strip()}
        return {'value':value}

    def _get_followup_level(self):
        sql = '''select ml.partner_id, l.id
                 from account_followup_followup_line l
                 left join account_move_line ml on ml.followup_line_id=l.id
                 where ml.partner_id in %s
                 order by l.sequence DESC'''
        self.env.cr.execute(sql, [tuple(self.ids)])
        res = self.env.cr.fetchall()
        rs = group(res, 0)
        for follow in self:
            follow.followup_max_level = rs.get(id) and rs[id][0][1] or False
     
    def _salesman_search(self, operator, value):
        if not len(value):
            return []
        u_ids = self.env['res.users'].search([('name', operator, value)])
        p_ids = self.env['res.partner'].search([('user_id', 'in' , u_ids.ids)])
        if not p_ids:
            return [('id', '=', '0')]
        return [('id', 'in', p_ids.ids)]
     
    ## TODO Convert to new API ?
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name.strip()
            if record.parent_id and not record.is_company:
                if record.type in ('default','invoice','other'):
                    if record.name.strip()[0:2] == '- ':
                        name = "%s %s" % (record.parent_name.strip(), name.strip())
                    else:
                        if not name:
                            if record.type == 'invoice':
                                name = "%s (invoice address)" % record.parent_name
                            elif record.type == 'other':
                                name = "%s (other address)" % record.parent_name
                            elif record.type == 'default':
                                name = "%s (default address)" % record.parent_name
                            else:
                                name = record.parent_name
                else:
                    name = "%s, %s" % ((record.lastname + ' ' + (record.firstname or '')).strip(), record.parent_name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res

    @api.depends('user_id')
    def _get_salesman(self):
        result = {}
        for rec in self:
            rec.user_id_readonly = rec.user_id.id
 
    #employee_nbr = fields.Integer('Nbr of Employee (Area)', help="Nbr of Employee in the area of the CCI")
    employee_nbr_total = fields.Integer('Nbr of Employee (Tot)', help="Nbr of Employee all around the world")
    invoice_paper = fields.Selection([('transfert belgian', 'Transfer belgian'), ('transfert iban', 'Transfer iban'), ('none', 'No printed transfert')], 'Bank Transfer Type', size=32)
    invoice_public = fields.Boolean('Invoice Public', default=1)
    invoice_special = fields.Boolean('Invoice Special', default=False)
    # new v8
    status_id = fields.Many2one('res.partner.state', string='Activity Status', help='State of activity of the partner')
    # end new v8
    #state_id2 = fields.Many2one('res.partner.state2', string='Customer State', help='status of the partner as a customer')
    reason_id = fields.Many2one('res.partner.reason', string='Reason')
    activity_description = fields.Text('Activity Description', translate=True)
    activity_code_ids = fields.One2many('res.partner.activity.relation', 'partner_id', string='Activity Codes')
    #export_procent = fields.Integer('Export(%)')
    #export_year = fields.Date('Export date', help='year of the export_procent value')
    #import_procent = fields.Integer('Import (%)')
    #import_year = fields.Date('Import Date', help='year of the import_procent value')
    invoice_nbr = fields.Integer('Nbr of invoice to print', help='number of additive invoices to be printed for this customer')
    #name_official = fields.Char('Official Name', size=80)
    #name_old = fields.Char('Former Name', size=80)
    #wall_exclusion = fields.Boolean('Not in Walloon DB', help='exclusion of this partner from the walloon database')
    # 'mag_send = fields.Selection([('never','Never'),('always','Always'),('managed_by_poste','Managed_by_Poste'),('prospect','Prospect')], 'Send mag.'),
    date_founded = fields.Date('Founding Date', help='Date of foundation of this company')
    training_authorization = fields.Char('Checks Auth.', size=12, help='Formation and Language Checks Authorization number')
    alert_advertising = fields.Boolean('Adv.Alert', help='Partners description to be shown when inserting new advertising sale')
    alert_events = fields.Boolean('Event Alert', help='Partners description to be shown when inserting new subscription to a meeting')
    alert_legalisations = fields.Boolean('Legal. Alert', help='Partners description to be shown when inserting new legalisation')
    alert_membership = fields.Boolean('Membership Alert', help='Partners description to be shown when inserting new ship sale')
    alert_others = fields.Boolean('Other alert', help='Partners description to be shown when inserting new sale not treated by _advertising, _events, _legalisations, _Membership')
    alert_explanation = fields.Text('Warning')
 
    #country_relation = fields.One2many('res.partner.country.relation', 'partner_id', string='Country Relation') we don't keep this field but the relation is kept only in res.partner.country.relation table
#     address = fields.One2many('res.partner', 'partner_id', 'Addresses')  # overridden just to change the name with "Addresses" instead of "Contacts"
    relation_ids = fields.One2many('res.partner.relation', 'current_partner_id', string='Partner Relation')
    canal_id = fields.Many2one('crm.tracking.medium', 'Favourite Channel')
    followup_max_level = fields.Many2one('account_followup.followup.line', compute='_get_followup_level', string='Max. Followup Level')
    article_ids = fields.Many2many('res.partner.article', 'res_partner_article_rel', 'partner_id', 'article_id', string='Articles')
    badge_partner = fields.Char('Badge Partner', size=128)
    user_id_readonly = fields.Many2one('res.users', compute='_get_salesman', search='_salesman_search', string='Salesman')
    turnover_last_12m = fields.Float('Turnover Last 12 Months', help="Turnover last 12 complete months, excluding the current one, without missions")
#     main_phone = fields.related('address', 'phone', type='char', string='Main Phone')
#     main_street = fields.related('address', 'street', type='char', string='Main street')
#     main_zipcode = fields.related('address', 'zip', type='char', string='Main Zip Code')
    write_date = fields.Datetime('Last Modification')
    write_uid = fields.Many2one('res.users', string='Last Modifier', help='The last person who has modified this address')
    # Never,Always,Managed_by_Poste,Prospect
#     # virement belge,virement iban
    
    # new fields to manage firstname/lastname on Contacts type and specific_address_id to manage link to specific address-child on type = contact and not is_company
    firstname = fields.Char("First name")
    lastname = fields.Char("Last name")
    specific_address_id = fields.Many2one('res.partner', string='Specific Address', help='Only if the working address is not the main address')

    function_label = fields.Char('Function Label', size=1024)
    function_code_label = fields.Char('Codes', size=128)
    function_codes = fields.Char('Function Codes')
    function_ids = fields.Many2many('res.partner.function','res_partner_functions_rel','partner_id','function_id', string='Functions')
    
    date_start = fields.Date(string='Date start')
    date_end = fields.Date(string='Date end')
    who_presence = fields.Boolean(string='In Whos Who')
    dir_presence = fields.Boolean(string='In Directory')
    department = fields.Char(string='Department', size=20)
    sequence_yearbook = fields.Integer(string='Sequence Yearbook', help='Sequence for printing in the Yearbook - 99 will not be printed', default=0)
    sequence_directory = fields.Integer(string='Sequence Directory', help='Sequence for printing in the Directory - 99 will not be printed', default=0)

    sequence_partner = fields.Integer(string='Sequence (Partner)', help='order of importance of this address in the list of addresses of the linked partner')
    notdelivered = fields.Date('Post Return', help='Date of return of mails not delivered at this address')

#     _sql_constraints = [
#         ('vat_uniq', 'unique (vat)', 'The VAT of the partner must be unique !')
#     ]

    @api.constrains('vat')
    def check_vat_number(self):
        partner_list = []
        other_partner = []
        for partner in self:
            if partner.vat:
                partner_list.append(partner.id)
                if partner.is_company and partner.child_ids:
                    for child in self.child_ids:
                        partner_list.append(child.id)
                else: # New code because of the new functionality in V8 (write the same VAT on the childs)
                    if partner.parent_id:
                        partner_list.append(partner.parent_id.id)
                        for child in partner.parent_id.child_ids:
                            partner_list.append(child.id)
                    else:
                        partner_list.append(partner.id)
                other_partner = self.search([('id', 'not in', partner_list), ('vat', '=', partner.vat)])
        if len(other_partner):
            raise Warning (_('Warning'), _('The VAT of the partner must be unique !'))

    #def onchange_phone(self, cr, uid, ids, phone):
    #    result = {}
    #    if phone:
    #        (cleaned_phonenr,extra) = self.env['res.partner'].unformat_phonenr(phone)
    #        (correct,nr_or_error_msg) = self.env['res.partner'].check_phonenr(cleaned_phonenr)
    #        if correct:
    #            print self.env['res.partner'].format_phonenr(phone)
    #            result['value'] = {'phone': self.env['res.partner'].format_phonenr(phone)}
    #        else:
    #            result['warning'] = {'title': _('Warning'),
    #                                 'message':nr_or_error_msg}
    #    return result

    #@api.multi
    #@api.onchange('phone')
    #def on_change_phone_num(self, value):
    #    (cleaned_phonenr,extra) = self.unformat_phonenr(value)
    #    (correct,nr_or_error_msg) = self.check_phonenr(cleaned_phonenr)
    #    if correct:
    #        value = {field_name:self.format_phonenr(value)}
    #        return {'value':value}
    #    else:
    #        raise Warning(_('Warning'), nr_or_error_msg)
    #        return False

#    @api.onchange('zip_id') 
#    def onchange_user_id(self):
#        # Changing the zip code can change the salesman
#        if not self or not self.zip_id:
#            return {}
#        if not self.parent_id.user_id:
#            if self.zip_id:
#                if self.type == 'default': 
#                    if self.zip_id.user_id:
#                        self.parent_id.write({'user_id': self.zip_id.user_id.id})

#class res_partner_zip_group_type(models.Model):
#    _name = 'res.partner.zip.group.type'
#    _description = 'res.partner.zip.group.type'
#
#    name = fields.Char('Name', size=50, required=True)
#
#class res_partner_zip_group(models.Model):
#    _name = 'res.partner.zip.group'
#    _description = 'res.partner.zip.group'
#    
#    type_id = fields.Many2one('res.partner.zip.group.type', string='Type')
#    name = fields.Char('Name', size=50, required=True)
#
#class res_partner_zip(models.Model):
#    _name = 'res.partner.zip'
#    _description = 'res.partner.zip'
#    
#    @api.constrains('groups_id')
#    def check_group_type(self):
#        for grp in self:
#            sql = '''
#            select group_id from partner_zip_group_rel1 where zip_id=%d
#            ''' % (grp.id)
#            self.env.cr.execute(sql)
#            groups = self.env.cr.fetchall()
#        list_group = []
#        for group in groups:
#            list_group.append(group[0])
#        data_zip = self.env['res.partner.zip.group'].browse(list_group)
#        list_zip = []
#        for data in data_zip:
#            if data.type_id.id in list_zip:
#                raise Warning(_('Error: Only one group of the same group type is allowed!'))
#            list_zip.append(data.type_id.id)
#        return True
#    
#    @api.multi
#    def name_get(self):
#        # will return zip code and city......
#        if not len(self):
#            return []
#        res = []
#        for r in self.read(['name', 'city']):
#            zip_city = str(r['name'] or '')
#            if r['name'] and r['city']:
#                zip_city += ' '
#            r['city'] = r['city'].encode('utf-8')
#            zip_city += str(r['city'] or '')
#            res.append((r['id'], zip_city))
#        return res
#    
#    name = fields.Char('Zip Code', size=10, required=True, index=1)
#    code = fields.Char('Zip Code', size=10) # required = True à ajouter une fois la migration terminée
#    city = fields.Char('City', size=60, translate=True, required=True)
#    partner_id = fields.Many2one('res.partner', string='Master Cci')
#    post_center_id = fields.Char('Post Center', size=40)
#    post_center_special = fields.Boolean(string='Post Center Special')
#    user_id = fields.Many2one('res.users', string='Salesman Responsible')
#    groups_id = fields.Many2many('res.partner.zip.group', 'partner_zip_group_rel1', 'zip_id', 'group_id', string='Areas')
#    distance = fields.Integer(string='Distance', help='Distance (km) between zip location and the cci.')
#    old_city = fields.Char(string='Old City Name', size=60)
#    country_id = fields.Many2one('res.country', string='Country') # required = True à ajouter après migration une fois tous les pays manquants retrouvés
    
#class res_partner_job(models.Model):
     # what to do with res.partner.job, res.partner.function
#     @api.multi
#     def unlink(self):
#         # Unlink related contact if: no other job AND not self_sufficient
#         for job in self:
#             super(res_partner_job, self).unlink()
#             data_contact = self.env['res.partner.contact'].browse(cr, uid, [id_contact])
#             if (not job.self_sufficent) and (not job.job_ids):
#                 data.unlink()
#         return True
#      
#     @api.model
#     def create(self, vals):
#         if vals.has_key('function_code_label') and vals['function_code_label']:
#             temp = ''
#             for letter in vals['function_code_label']:
#                 res = self.env['res.partner.function'].search([('code', '=', letter)], limit=1)
#                 if res:
#                     temp += res.code
#             vals['function_code_label'] = temp or vals['function_code_label']
#         if 'function_id' in vals and not vals['function_id']:
#             vals['function_id'] = self.env['res.partner.function'].search([], limit=1).id
#         return super(res_partner_job, self).create(vals)
#      
#     @api.multi
#     def write(self):
#         if vals.has_key('function_code_label') and vals['function_code_label']:
#             temp = ''
#             for letter in vals['function_code_label']:
#                 res = self.env['res.partner.function'].search([('code', '=', letter)], limit=1)
#                 if res:
#                     temp += res.code
#             vals['function_code_label'] = temp or vals['function_code_label']
#         if 'function_id' in vals and not vals['function_id']:
#             vals['function_id'] = self.env['res.partner.function'].search([], limti=1)
#         return super(res_partner_job, self).write(vals)
     

#class res_partner(models.Model):
#    _inherit = 'res.partner'
#    _description = 'res.partner'
#    
#    @api.model
#    def create(self, vals):
#        if vals.has_key('zip_id') and vals['zip_id']:
#            vals['zip'] = self.env['res.partner.zip'].browse(vals['zip_id']).name
#            vals['city'] = self.env['res.partner.zip'].browse(vals['zip_id']).city
#        return super(res_partner_address, self).create(vals)
#    
#    @api.multi
#    def write(self, vals):
#        if vals.has_key('zip_id') and vals['zip_id']:
#            vals['zip'] = self.env['res.partner.zip'].browse(vals['zip_id']).name
#            vals['city'] = self.env['res.partner.zip'].browse(vals['zip_id']).city
#        return super(res_partner_address, self).write(vals)
# 
#    @api.one
#    def get_city(self):
#        return self.zip_id.city
#    
# que faire du name?
 
#    def _get_name(self, cr, uid, ids, name, arg, context={}):
 #       res={}
  #      for add in self.browse(cr, uid, ids, context):
   #           if add.contact_id:
    #              res[add.id] = (add.department or '') + ' ' + add.contact_id.name
     #         else:
      #            res[add.id] = add.department
       # return res
    
class res_partner_activity_list(models.Model):  # new object added!
    _name = 'res.partner.activity.list'
    _description = 'res.partner.activity.list'
    
    name = fields.Char(string='Code list', size=256, required=True)
    abbreviation = fields.Char(string='Abbreviation', size=16)

class res_partner_activity(models.Model):  # modfiy res.activity.code to res.partner.activity
    _name = 'res.partner.activity'
    _description = 'res.partner.activity'
    _rec_name = 'code'
    
    @api.multi
    def name_get(self):
        # return somethong like”list_id.abbreviation or list_id.name – code”
        res = []
        for act in self:
            res.append((act.id, (act.code or '') + ' - ' + (act.label or '')))
#        data_activity = self.read(cr, uid, ids, ['list_id','code'], context)
#        res = []
#        list_obj = self.pool.get('res.partner.activity.list')
#        for read in data_activity:
#            if read['list_id']:
#                data=list_obj.read(cr, uid, read['list_id'][0],['abbreviation','name'], context)
#                if data['abbreviation']:
#                    res.append((read['id'], data['abbreviation']))
#                else:
#                    str=data['name']+'-'+read['code']
#                    res.append((read['id'],str))
        return res

    code = fields.Char('Code', size=6, required=True)
    label = fields.Char('Label', size=250, transtale=True, required=True)
    description = fields.Text('Description')
    code_relations = fields.Many2many('res.partner.activity', 'res_activity_code_rel', 'code_id1', 'code_id2', string='Related codes')
    # 'partner_id = fields.Many2one('res.partner','Partner')
    list_id = fields.Many2one('res.partner.activity.list', string='List', required=True)

class res_partner_map_activity(models.Model):
    _name = 'res.partner.map.activity'
    _description = 'res.partner.map.activity'
    _rec_name = 'activity_n_id'

    activity_pj_id = fields.Many2one('res.partner.activity', string='Activity PJ', ondelete='cascade')
    activity_n_id = fields.Many2one('res.partner.activity', string='Activity N', ondelete='cascade')

class res_partner_activity_relation(models.Model):
    _name = 'res.partner.activity.relation'
    _description = 'res.partner.activity.relation'
    _rec_name = 'activity_id'
    
    @api.model
    def default_get(self, fields):
        data = super(res_partner_activity_relation, self).default_get(fields)
        if self.env.context.get('activities'):
            map_obj = self.env['res.partner.map.activity']
            done = []
            for i in self.env.context['activities']:
                if i[2]:
                    if i[2]['activity_id']:
                        activity_id = i[2]['activity_id']
                        activity_ids = map_obj.search(['|', ('activity_pj_id', '=', activity_id), ('activity_n_id', '=', activity_id)])
                        if activity_ids:
                            for activ_item in activity_ids:
                                if activ_item.activity_pj_id.id == activity_id and (activ_item.activity_pj_id.id not in done):
                                    data['activity_id'] = activ_item.activity_n_id.id
                                    done.append(activ_item.activity_n_id.id)
                                elif activ_item.activity_n_id.id == activity_id and (activ_item.activity_n_id.id not in done):
                                    data['activity_id'] = activ_item.activity_pj_id.id
                                    done.append(activ_item.activity_pj_id.id)
        return data

    importance = fields.Selection([('main', 'Main'), ('primary', 'Primary'), ('secondary', 'Secondary')], string='Importance', required=True, default='main')
    activity_id = fields.Many2one('res.partner.activity', string='Activity', ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete="cascade")
    
class res_partner_function(models.Model):
    _name = 'res.partner.function'
    _description = 'Function of the contact'
    
    name = fields.Char('Name',size=64,required=True)
    code = fields.Char('Code',size=8,required=True)

    @api.multi
    def name_get(self):
        reads = self.read(['code', 'name'])
        res = []
        for record in reads:
            res.append((record['id'], u'%s (%s)' % (record['name'],record['code'])))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=None):
        args = args or []
        if name:
            args = args + ['|',('name', operator, name),('code', '=', name)]
        functions = self.search(args, limit=limit)
        return functions.name_get()
        
class res_partner_relation_type(models.Model):
    _name = 'res.partner.relation.type'
    _description = 'res.partner.relation.type'

    name = fields.Char('Contact', size=50, required=True)

class res_partner_relation(models.Model):
    _name = "res.partner.relation"
    _description = 'res.partner.relation'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    current_partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    description = fields.Text('Description')
    percent = fields.Float('Ownership')
    type_id = fields.Many2one('res.partner.relation.type', string='Type', required=True)

class res_partner_country_relation(models.Model):
    _name = "res.partner.country.relation"
    _description = 'res.partner.country.relation'
   
    frequency = fields.Selection([('frequent', 'Frequent'), ('occasional', 'Occasionnel'), ('prospect', 'Prospection')], string='Frequency')
    partner_id = fields.Many2one('res.partner', string='Partner')
    country_id = fields.Many2one('cci.country', string='Country')
    type = fields.Selection([('export', 'Export'), ('import', 'Import'), ('saloon', 'Salon'), ('representation', 'Representation'), ('expert', 'Expert')], string='Types')

class res_partner_contact(models.Model):
    
    @api.multi
    def on_change_phone_num(self, phone):
        return check_phone_num(phone)
 
    _inherit = 'res.partner'
     
    article_ids = fields.Many2many('res.partner.article', 'res_partner_contact_article_rel', 'contact_id', 'article_id', string='Articles')
    fse_zip_id = fields.Many2one('res.partner.zip', 'FSE Private Zip Code')

class res_partner_photo(models.Model):
    _name = 'res.partner.photo'
    _order = 'date desc'
    
    partner_chg_ids = fields.One2many('res.partner.change', 'photo_id', string='Partner Changes')
    address_chg_ids = fields.One2many('res.partner.address.change', 'photo_id', string='Address Changes')
    partner_new_ids = fields.One2many('res.partner.address.new', 'photo_id', string='New Partners')
    partner_state_ids = fields.One2many('res.partner.state.register', 'photo_id', string='State Changes')
    partner_lost_ids = fields.One2many('res.partner.address.lost', 'photo_id', string='Losts')
    name = fields.Char(string='Photo Name', size=164, index=True)  # default='Photo' + fields.Date.context_today
    date = fields.Date(string='Date', size=64, index=True, default=fields.Date.context_today)

class res_partner_state_register(models.Model):
    _name = 'res.partner.state.register'
    
    name = fields.Char('Code', size=64, index=True)
    old_state = fields.Many2one('res.partner.state', string='Old State')
    new_state = fields.Many2one('res.partner.state', string='New State')
    partner_id = fields.Many2one('res.partner', string='Partner Name')
    address_id = fields.Many2one('res.partner', string='Address')
    photo_id = fields.Many2one('res.partner.photo', string='Photo', ondelete="cascade")

class res_partner_address_change(models.Model):
    _name = 'res.partner.address.change'
    
    code = fields.Char('Code', size=64)
    name = fields.Many2one('res.partner', string='Partner Name')
    old_address = fields.Char('Old Address', size=264)
    new_address = fields.Char('New Address', size=264)
    address_id = fields.Many2one('res.partner', string='Address')
    photo_id = fields.Many2one('res.partner.photo', string='Photo', ondelete="cascade")

class res_partner_change(models.Model):
    _name = 'res.partner.change'
    
    code = fields.Char(string='Code', size=64)
    name = fields.Char(string='New Name', size=264)
    old_name = fields.Char(string='Old Name', size=264)
    address_id = fields.Many2one('res.partner', string='Address')
    photo_id = fields.Many2one('res.partner.photo', string='Photo', ondelete="cascade")

class res_partner_address_new(models.Model):
    _name = 'res.partner.address.new'
    _rec_name = 'code'
    
    code = fields.Char('Code', size=64)
    address = fields.Char(string='Postal Address', size=264)
    state_activity = fields.Many2one('res.partner.state', string='State Activity')
    name = fields.Many2one('res.partner', string='Partner')
    address_id = fields.Many2one('res.partner', string='Address')
    photo_id = fields.Many2one('res.partner.photo', string='Photo', ondelete='cascade')

class res_partner_address_lost(models.Model):
    _name = 'res.partner.address.lost'
    
    name = fields.Char(string='Code', size=64)
    state_activity = fields.Many2one('res.partner.state', string='State Activity')
    address_id = fields.Many2one('res.partner', string='Address')
    partner_id = fields.Many2one('res.partner', string='Partner')
    photo_id = fields.Many2one('res.partner.photo', string='Photo', ondelete='cascade')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

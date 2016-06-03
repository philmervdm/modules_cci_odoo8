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
from xlwt import *

from itertools import groupby
from operator import itemgetter

from openerp import models, fields, api, _
from openerp.exceptions import Warning

def group(lst, col):
    return dict((k, [v for v in itr]) for k, itr in groupby(sorted(lst, key=lambda x: x[col]), itemgetter(col)))

def check_phone_num(phone):
    if not phone:
        return {}
    result = {}
    gsm_num = ['0470', '0471', '0472', '0473', '0474', '0475', '0476', '0477', '0478', '0479', '0484', '0485', '0486', '0487', '0488', '0489', '0492', '0493', '0494', '0495', '0496', '0497', '0498', '0499']
    if not phone.startswith('00'):
        is_gsm = False
        for item in gsm_num:
            is_gsm = phone.startswith(item)
            if is_gsm:
                break
        if is_gsm:
            if not len(phone) == 10:
                raise Warning(_('Validate Error'),
                    _('Invalid GSM Phone number. Only 10 figures numbers are allowed.'))
        else:
            if not len(phone) == 9:
                raise Warning(_('Validate Error'),
                    _('Invalid Phone number. Only 9 figures numbers are allowed.'))
    result['phone'] = phone
    return {'value': result}

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

class res_partner_state2(models.Model):
    _name = 'res.partner.state2'
    _description = 'res.partner.state2'

    name = fields.Char('Customer Status', size=50, required=True)

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
        
    @api.model
    def calculate_type_customer(self, excluded_accounts=[], additional_accounts=[], letters_range=[25, 9], digits_range=[5000, 1000, 0], last_period_id=None):
        # get the concerned accounts
        account_ids = self.env['account.account'].search([('code', 'like', '7')])  # first screening to get all accounts with '7' inside
        accounts = account_ids.read(['code', 'id'])
        selected_accounts = []
        for account in accounts:
            if account['code'][0] == '7' and account['id'] not in excluded_accounts:
                selected_accounts.append(account['id'])
        for id in additional_accounts:
            if id not in selected_accounts:
                selected_accounts.append(id)
        # get the concerned periods, if not given as parameters, the last month excluding the current one
        obj_period = self.env['account.period']

        if not last_period_id:
            today = datetime.date.today()
            year = today.year
            month = today.month
            month -= 1
            if month <= 0:
                month += 12
                year -= 1
            last_month_date = datetime.datetime(year, month, 28).strftime('%Y-%m-%d')
            last_period = obj_period.search([('date_start', '<=', last_month_date), ('date_stop', '>=', last_month_date), ('special', '=', False)], limit=1)
            last_period_id = last_period.id
            
        last_period = obj_period.browse(last_period_id)
        
        if int(last_period.date_start[5:7]) < 12:
            start_first_period = str(int(last_period.date_start[0:4]) - 1) + '-' + str(int(last_period.date_start[5:7]) + 1).rjust(2, '0') + '-01'
        else:
            start_first_period = last_period.date_start[0:4] + '-01-01'
        period_ids = obj_period.search([('special', '=', False), ('date_start', '>=', start_first_period), ('date_stop', '<=', last_period.date_stop)])
        # get the concerned journals
        journal_ids = self.env['account.journal'].search([('type', '=', 'sale')])
        # sum the turnover by partner
        cjournals = '(' + (','.join([str(x) for x in journal_ids.ids])) + ')'
        cperiods = '(' + (','.join([str(x) for x in period_ids.ids])) + ')'
        caccounts = '(' + (','.join([str(x) for x in selected_accounts])) + ')'
        sql = """SELECT partner_id, SUM( credit-debit ) as turnover 
                    from account_move_line
                    where journal_id in %s and period_id in %s and account_id in %s group by partner_id""" % (cjournals, cperiods, caccounts)
        self.env.cr.execute(sql)        
        res = self.env.cr.fetchall()
        turnovers = {}
        
        for line in res:
            turnovers[line[0]] = line[1]
        # get the categs ids
        categs = {}
        categ_ids = []
        obj_categ = self.env['res.partner.category']
        for name in ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4']:
            categ = obj_categ.search([('name', 'like', 'Type Client ' + name)], limit=1)
            if len(categ) == 1:
                categs[name] = categ.id
                categ_ids.append(categ.id)
        obj_partner = self.env['res.partner']
        partners = obj_partner.search([])
        partner_datas = partners.read(['id', 'turnover_last_12m', 'category_id', 'employee_nbr'])
        count = 0
        for part in partner_datas:
            # for each partner we must calcule the new categ
            newletter = 'C'
            if part['employee_nbr'] > letters_range[0]:
                newletter = 'A'
            elif part['employee_nbr'] > letters_range[1]:
                newletter = 'B'
            if part['id'] in turnovers:
                newturnover = turnovers[part['id']]
                newdigit = '4'
                if newturnover > digits_range[0]:
                    newdigit = '1'
                elif newturnover > digits_range[1]:
                    newdigit = '2'
                elif newturnover > digits_range[2]:
                    newdigit = '3'
                newvalues = {'turnover_last_12m': newturnover, 'categ_customer_id': categs.get(newletter + newdigit) }
            else:
                newvalues = {'turnover_last_12m': 0.0, 'categ_customer_id': categs.get(newletter + '4') }
            # then we must verify if this partner has already the same turnover, and the right category and no others 'customer type category'
            lModify = False
            if part['turnover_last_12m'] <> newvalues['turnover_last_12m']:
                lModify = True
            else:
                lOthers = False
                lAlready = False
                for categ_id in categ_ids:
                    if categ_id in part['category_id']:
                        if categ_id == newvalues['categ_customer_id']:
                            lAlready = True
                        else:
                            lOthers = True
                if lOthers or not lAlready:
                    lModify = True
            if lModify:
                # if something has changed, we must write the new values in the partner table
                count += 1
                # we take all the categs not of the type 'Type of customer'
                new_categs = []
                for id in part['category_id']:
                    if id not in categ_ids:
                        new_categs.append(id)
                # we add the new one
                new_categs.append( newvalues['categ_customer_id'] )
                self.write({'turnover_last_12m':newvalues['turnover_last_12m'],'category_id':[(6,0,new_categs)]} )
        return 'The result of the re-calculation is ' + str(count) + ' partners changed.'
    
    @api.model
    def export_members_excel(self, category_id=False, ftp=False):
        def get_phone_country_prefix():
            result = []
            obj_country = self.env['cci.country']
            country_ids = obj_country.search([('phoneprefix', '!=', False), ('phoneprefix', '!=', 0)])
            if country_ids:
                countries = country_ids.read(['phoneprefix'])
                result = [str(x['phoneprefix']) for x in countries]
            return result
        
        def convert_phone(string, PHONE_COUNTRY_PREFIX):
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
                    # print string
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
        
        if category_id:
            # extract all ids of activity sector categories and remove '[303]' from name
            obj_categ = self.env['res.partner.category']
            old_len = 0
            categ_ids = [category_id]
            while len(categ_ids) > old_len:
                new_ids = categ_ids[old_len:]  # ids of categories added last time
                new_categories = obj_categ.browse(new_ids)
                old_len = len(categ_ids)  # the new frontier ...
                new_categs = new_categories.read(['child_ids'])
                for categ in new_categs:
                    if categ['child_ids']:
                        categ_ids.extend(categ['child_ids'])
            
            categoires = obj_categ.browse(categ_ids)
            categs = categoires.read(['name'])
            dCategs = {}
            for categ in categs:
                formated_name = categ['name']
                posA = formated_name.rfind('[')
                posB = formated_name.rfind(']')
                if posA > 0 and posB > 0 and posA < posB:
                    formated_name = formated_name[0:posA - 1]
                dCategs[ categ['id'] ] = formated_name
 
        # extract all active members
        obj_partner = self.env['res.partner']
        partners = obj_partner.search([('activ_state_id', '=', 1),])
        wb = Workbook()
        ws = wb.add_sheet('liste')
        ws.write(0, 0, u'Entreprise')
        ws.write(0, 1, u'Adresse')
        ws.write(0, 2, u'Adresse2')
        ws.write(0, 3, u'CP')
        ws.write(0, 4, u'Localité')
        ws.write(0, 5, u'Tél')
        ws.write(0, 6, u'Fax')
        ws.write(0, 7, u'Fonction')
        ws.write(0, 8, u'Nom')
        ws.write(0, 9, u'Prénom')
        ws.write(0, 10, u'Civilité')
        ws.write(0, 11, u'Effectif')
        ws.write(0, 12, u'TVA')
        if category_id:
            ws.write(0, 13, u'Secteur')
        line = 1
        PREFIXES = get_phone_country_prefix()
        for partner in partners:
            ws.write(line, 0, partner.name)
            for address in partner.child_ids:
                if address.type == 'default':
                    ws.write(line, 1, address.street or '')
                    ws.write(line, 2, address.street2 or '')
                    ws.write(line, 3, address.zip or '')
                    ws.write(line, 4, address.city or '')
                    ws.write(line, 5, convert_phone(address.phone or '', PREFIXES))
                    ws.write(line, 6, convert_phone(address.fax or '', PREFIXES))
                    min_seq = 999
                    id_min_seq = False
                    id_seq0 = False
                    for job in address.other_contact_ids:
                        if job.sequence_yearbook < min_seq and job.sequence_yearbook > 0:
                            min_seq = job.sequence_yearbook
                            id_min_seq = job.id
                        if not id_seq0 and job.sequence_yearbook == 0:
                            id_seq0 = job.id
                    if id_min_seq or id_seq0:
                        selected_job_id = id_seq0
                        if id_min_seq:
                            selected_job_id = id_min_seq
                        for job in address.other_contact_ids:
                            if job.id == selected_job_id:
                                ws.write(line, 7, job.function_label or '')
                                if job.contact_id:
                                    ws.write(line, 8, job.contact_id.name)
                                    ws.write(line, 9, job.contact_id.first_name or '')
                                    ws.write(line, 10, job.contact_id.title or '')
                    break
            ws.write(line, 11, max(0, partner.employee_nbr or 0) or 'nc')
            ws.write(line, 12, partner.vat or '')
            if category_id:
                for categ in partner.category_id:  # # category_id is, not like his name define, an array of category ids
                    if categ.id in categ_ids:
                        ws.write(line, 13, dCategs[categ.id])
                        break
            line += 1
        wb.save('repertoire_des_membres_excel.xls')
        # wb.save('test.xls')
        wb = None
 
        # export to FTP
        if ftp:
            import ftplib
            FTP_HOST = '212.166.5.117'
            FTP_USER = 'ccilv_files'
            FTP_PW = 'hid5367cx'
            FTP_CWD = 'Repertoire_des_Membres'
            lFiles = []
            ftp = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PW)
            ftp.getwelcome()
            ftp.pwd()
            ftp.retrlines('LIST')
            ftp.cwd(FTP_CWD)
            hFile = open('repertoire_des_membres_excel.xls' , 'rb')
            # hFile = open( 'test.xls' ,'rb')
            result = ftp.storbinary('STOR ' + 'repertoire_des_membres.xls', hFile)
            hFile.close()
            ftp.quit()
        # get the concerned accounts
        account_ids = self.env['account.account'].search([('code', 'like', '7')])  # first screening to get all accounts with '7' inside
        accounts = account_ids.read(['code', 'id'])
     
    @api.model
    def create(self, vals):
        if vals.has_key('vat') and vals['vat']:
            vals.update({'vat':vals['vat'].upper()})
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
     
    @api.model
    def _get_customer_state(self):
        ids = self.env['res.partner.state2'].search([('name', 'like', 'Imputable')], limit=1)
        return ids
     
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
     
    @api.depends('user_id')
    def _get_salesman(self):
        result = {}
        for rec in self:
            rec.user_id_readonly = rec.user_id.id
 
    #employee_nbr = fields.Integer('Nbr of Employee (Area)', help="Nbr of Employee in the area of the CCI")
    employee_nbr_total = fields.Integer('Nbr of Employee (Tot)', help="Nbr of Employee all around the world")
    invoice_paper = fields.Selection([('transfert belgian', 'Transfer belgian'), ('transfert iban', 'Transfer iban'), ('none', 'No printed transfert')], 'Bank Transfer Type', size=32)
    invoice_public = fields.Boolean('Invoice Public', default=1)
    invoice_special = fields.Boolean('Invoice Special', default=_get_customer_state)
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
    dir_name = fields.Char('Name in Member Dir.', size=250, help='Name under wich the partner will be inserted in the members directory')
    dir_name2 = fields.Char('1st Shortcut name ', size=250, help='First shortcut in the members directory, pointing to the dir_name field')
    dir_name3 = fields.Char('2nd Shortcut name ', size=250, help='Second shortcut')
    dir_date_last = fields.Date('Partner Data Date', help='Date of latest update of the partner data by itself (via paper or Internet)')
    dir_date_accept = fields.Date("Good to shoot Date", help='Date of last acceptation of Bon a Tirer')
    dir_presence = fields.Boolean('Dir. Presence', help='Present in the directory of the members')
    dir_date_publication = fields.Date('Publication Date')
    dir_exclude = fields.Boolean('Dir. exclude', help='Exclusion from the Members directory')
 
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
    
class res_partner_job(models.Model):
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
     
    @api.model
    def on_change_phone_num(self, phone):
        return check_phone_num(self, phone)
 
    _inherit = 'res.partner'
         
    function_label = fields.Char('Function Label', size=1024)
    function_code_label = fields.Char('Codes', size=128)
    date_start = fields.Date(string='Date start')
    date_end = fields.Date(string='Date end')
#     canal_id = fields.Many2one('res.partner.canal', string='Canal', help='favorite channel for communication')
#     active = fields.Boolean('Active', default=True)
    who_presence = fields.Boolean(string='In Whos Who')
    dir_presence = fields.Boolean(string='In Directory')
    department = fields.Char(string='Department', size=20)
    sequence_yearbook = fields.Integer(string='Sequence Yearbook', help='Sequence for printing in the Yearbook - 99 will not be printed', default=0)
    sequence_directory = fields.Integer(string='Sequence Directory', help='Sequence for printing in the Directory - 99 will not be printed', default=0)

class res_partner_address(models.Model):
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
    
    @api.multi
    def on_change_phone_num(self, phone):
        return check_phone_num(self, phone)
 
    # 'name =  fields.function(_get_name, method=True, string='Contact Name',type='char',size=64)#override parent field
    state = fields.Selection([('correct', 'Correct'), ('to check', 'To check')], string='Code', default='correct')
    active = fields.Boolean('Active', default=1)
    sequence_partner = fields.Integer(string='Sequence (Partner)', help='order of importance of this address in the list of addresses of the linked partner')
#     write_date = fields.Datetime('Last Modification')
#     write_uid = fields.Many2one('res.users', string='Last Modifier', help='The last person who has modified this address')
    activity_description = fields.Text('Local Activity Description', translate=True)
    local_employee = fields.Integer('Nbr of Employee (Site)', help="Nbr of Employee in the site (for the directory)")
    dir_show_name = fields.Char('Directory Shown Name', size=128, help="Name of this address printed in the directory of members")
    dir_sort_name = fields.Char('Directory Sort Name', size=128, help="Name of this address used to sort the partners in the directory of members")
#     dir_exclude = fields.Boolean('Directory exclusion', help='Check this box to exclude this address of the directory of members')
    notdelivered = fields.Date('Post Return', help='Date of return of mails not delivered at this address')
    
    @api.onchange('zip_id') 
    def onchange_user_id(self):
        # Changing the zip code can change the salesman
        if not self or not self.zip_id:
            return {}
        if not self.parent_id.user_id:
            if self.zip_id:
                if self.type == 'default': 
                    if self.zip_id.user_id:
                        self.parent_id.write({'user_id': self.zip_id.user_id.id})

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
    
# class res_partner_function(models.Model):
#     _inherit = 'res.partner.function'
#     _description = 'Function of the contact inherit'
#     
#     @api.multi
#     def name_get(self):
#         if not len(ids):
#             return []
#         reads = self.read(['code', 'name'])
#         res = []
#         str1 = ''
#         for record in reads:
#             if record['name'] or record['code']:
#                 str1 = record['name'] + '(' + (record['code'] or '') + ')'
#             res.append((record['id'], str1))
#         return res

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

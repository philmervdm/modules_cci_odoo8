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
import datetime
from openerp import api, fields, models, _
from openerp.exceptions import Warning
from xlwt import *
import base64


class membership_calls_2_excel(models.TransientModel):
    _name = 'membership.calls_2_excel'

    year = fields.Integer(string='New year', help='New year of the called membership...', required=True,
                          default=datetime.datetime.today().year + 1)
    address_type = fields.Selection([('default', 'Default address'),
                                     ('invoice', 'Invoice address otherwise default address'),
                                     ('contact_default', 'Membership Contact else default address'),
                                     ('contact_invoice', 'Membership Contact else invoice address otherwise default address')],
                                    string='Type of address', default='invoice')
    also_invoiced = fields.Boolean(string='Also the invoiced members, else only paid')
    job_categs = fields.Char(string='Categories of searched contacts', size=20, required=True)
    price_site = fields.Float(string='W/o VAT Price per Site', digit=(15, 2), required=True)

    def get_phone_country_prefix(self):
        result = []
        obj_country = self.env['cci.country']
        countries = obj_country.search([('phoneprefix', '!=', False), ('phoneprefix', '!=', 0)])
        if countries:
            result = [x.phoneprefix for x in countries]
        return result

    def convert_phone(self, string, PHONE_COUNTRY_PREFIX):
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
                        result = '+' + string[2:2+len(prefix)] + ' ' + string[2+len(prefix):4+len(prefix)]
                        rest = string[4+len(prefix):]
                        while len(rest) > 3:
                            result += '.' + rest[0:2]
                            rest = rest[2:]
                        result += '.' + rest
                    else:
                        result = 'International:'+string
        return result

    @api.multi
    def open_window_results(self):
        # manage parameters
        if not self.year:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.year and self.year < 1900:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.also_invoiced:
            mstates = ['invoiced', 'paid']
        else:
            mstates = ['paid']
        unit_price = self.price_site
        address_type = self.address_type
        if address_type[0:8] == 'contact_':
            if len(self.job_categs) > 0:
                membership_categ = self.job_categs[0]
            else:
                address_type = address_type[8:]  # we forget to search on membership categ because this is not givent as parameters
        if len(self.job_categs) == 0:
            categs = 'G'
            len_categs = 1
        else:
            categs = self.job_categs
            len_categs = len(categs)
        # get the usual VAT on membership
        tax_rate = 0.0
        mprod_obj = self.env['product.product']
        mprods = mprod_obj.search([('membership', '=', True), ('membership_year', '=', self.year)])
        if mprods:
            for mproduct in mprods:
                if mproduct.product_tmpl_id.taxes_id:
                    tax_rate = mproduct.product_tmpl_id.taxes_id[0].amount
                    if tax_rate > 0.0:
                        break;
        # prepare the inserting of new data
        PREFIXES = self.get_phone_country_prefix()
        # get the data about all contact title
        title_obj = self.env['res.partner.title']
        title_ids = title_obj.search([('domain', '=', 'contact')])
        titles = title_ids.read(['id', 'shortcut', 'name', 'other1', 'other2'])
        dTitles = {}
        for tit in titles:
            dTitles[tit['shortcut']] = tit
        # get the data about all the salesman from cci_salesman.cci.contact
        salesman_obj = self.env['res.users']
        salesmen = salesman_obj.search([])
#         salesmen = salesman_obj.browse(cr,uid,salesman_ids)
        dSalesman = {}
        for sman in salesmen:
            dSalesman[sman.id] = sman
        # get this list of partners already invoiced for the next year of membership
        # event the inactive products
        mprod_ids = mprod_obj.search([('membership', '=', True),
                                      ('membership_year', '=', self.year),
                                      '|', ('active', '=', True), ('active', '=', False)])
        excluded_partner_ids = []
        if len(mprod_ids) > 0:
            selection = "SELECT distinct(partner_id) \
            FROM account_move_line \
            where product_id in (%s)" % ','.join([str(x) for x in mprod_ids.ids])
            self.env.cr.execute(selection)
            partners = self.env.cr.fetchall()
            excluded_partner_ids = [x[0] for x in partners]
        # get all partners concerned
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([('membership_state', 'in', mstates),
                                       ('state_id', '=', 1),
                                       ('membership_amount', '>', 0.1),
                                       ('refuse_membership', '=', False),
                                       ('free_member', '=', False),
                                       ('associate_member', '=', False)])
        wb1 = Workbook()
        ws1 = wb1.add_sheet('Appels')
        ws1.write(0, 0, u'partner_id')
        ws1.write(0, 1, u'address_id')
        ws1.write(0, 2, u'job_id')
        ws1.write(0, 3, u'contact_id')
        ws1.write(0, 4, u'partner_name')
        ws1.write(0, 5, u'street')
        ws1.write(0, 6, u'street2')
        ws1.write(0, 7, u'zip_code')
        ws1.write(0, 8, u'city')
        ws1.write(0, 9, u'email_addr')
        ws1.write(0, 10, u'phone_addr')
        ws1.write(0, 11, u'fax_addr')
        ws1.write(0, 12, u'name')
        ws1.write(0, 13, u'first_name')
        ws1.write(0, 14, u'courtesy')
        ws1.write(0, 15, u'title')
        ws1.write(0, 15, u'title_categs')
        ws1.write(0, 17, u'email_contact')
        ws1.write(0, 18, u'base_amount')
        ws1.write(0, 19, u'count_add_sites')
        ws1.write(0, 20, u'unit_price_site')
        ws1.write(0, 21, u'desc_add_site')
        ws1.write(0, 22, u'wovat_amount')
        ws1.write(0, 23, u'wvat_amount')
        ws1.write(0, 24, u'salesman')
        ws1.write(0, 25, u'salesman_phone')
        ws1.write(0, 26, u'salesman_fax')
        ws1.write(0, 27, u'salesman_mobile')
        ws1.write(0, 28, u'salesman_email')
        ws1.write(0, 29, u'vcs')
        ws1.write(0, 30, u'courtesy1')
        ws1.write(0, 31, u'courtesy2')
        line = 1
        for partner in partners:
            if partner.id not in excluded_partner_ids:
                # search the first good address in the order of sequence_address (witch is the order of appearance in partner.address
                # beware : some partner_sequence = false => 99
                good_address = False
                if partner.address:
                    # first, try to find the address containing the membership contact categ
                    if address_type[0:8] == 'contact_':
                        for address in partner.child_ids:
                            if address.other_contact_ids:
                                for job in address.other_contact_ids:
                                    if job.function_code_label and membership_categ in job.function_code_label:
                                        good_address = address
                                        break;
                    # second (of first if contact_ if not asked), try to fin the first address of the good type
                    if not good_address:
                        if address_type == 'default':
                            for addr in partner.child_ids:
                                if addr.type == 'default':
                                    good_address = addr
                                    break;
                        else:
                            for addr in partner.child_ids:
                                if addr.type == 'invoice':
                                    good_address = addr
                                    break;
                                else:
                                    if not good_address:
                                        good_address = addr
                                        # not break; because we must continue to search after an 'invoice' type
                if good_address:
                    # search for the first job-contact in this address with a good categ
                    lFoundJob = False
                    iCurrent = 0
                    while not lFoundJob and iCurrent < len_categs:
                        current_categ = categs[iCurrent]
                        for job in good_address.other_contact_ids:
                            if current_categ in (job.function_code_label or '') and job.contact_id.id > 0:
                                sel_job = job
                                sel_contact = job.contact_id
                                lFoundJob = True
                                break;
                        iCurrent += 1
                    # manage special values
                    selected_email = ''
                    if lFoundJob:
                        if sel_job.email:
                            selected_email = sel_job.email
                        elif sel_contact.email:
                            selected_email = sel_contact.email
                    if partner.user_id.id in dSalesman:
                        salesman = dSalesman[partner.user_id.id]
                    else:
                        salesman = False
                    global_name = ''
                    if good_address.name and len(good_address.name) > 0:
                        if good_address.name[0] == '-':
                            global_name = partner.name.strip() + ' ' + good_address.name.strip()
                        else:
                            global_name = good_address.name
                    else:
                        global_name = partner.name
                    if partner.property_account_position:
                        current_tax_rate = 0.0
                    else:
                        current_tax_rate = tax_rate
                    courtesy1 = ''
                    courtesy2 = ''
                    if lFoundJob and sel_contact.title and dTitles.has_key(sel_contact.title):
                        courtesy1 = dTitles[sel_contact.title]['other1'] or ''
                        courtesy2 = dTitles[sel_contact.title]['other2'] or ''
                    # record the data
                    ws1.write(line, 0, partner.id)
                    ws1.write(line, 1, good_address.id)
                    ws1.write(line, 2, lFoundJob and sel_job.id or 0)
                    ws1.write(line, 3, lFoundJob and sel_contact.id or 0)
                    ws1.write(line, 4, global_name)
                    ws1.write(line, 5, good_address.street or '')
                    ws1.write(line, 6, good_address.street2 or '')
                    ws1.write(line, 7, good_address.zip_id.name or '')
                    ws1.write(line, 8, good_address.zip_id.city or '')
                    ws1.write(line, 9, good_address.email or '')
                    ws1.write(line, 10, self.convert_phone(good_address.phone or '', PREFIXES))
                    ws1.write(line, 11, self.convert_phone(good_address.fax or '', PREFIXES))
                    ws1.write(line, 12, lFoundJob and sel_contact.name or '')
                    ws1.write(line, 13, lFoundJob and (sel_contact.first_name or '') or '')
                    ws1.write(line, 14, lFoundJob and (sel_contact.title or '') or '')
                    ws1.write(line, 15, lFoundJob and (sel_job.function_label or '') or '')
                    ws1.write(line, 16, lFoundJob and sel_job.function_code_label or '')
                    ws1.write(line, 17, selected_email)
                    ws1.write(line, 18, partner.membership_amount or 0.0)
                    ws1.write(line, 19, partner.site_membership or 0)
                    ws1.write(line, 20, unit_price)
                    ws1.write(line, 21, partner.desc_add_site or '')
                    ws1.write(line, 22,(partner.membership_amount or 0.0) + ((partner.site_membership or 0) * unit_price))
                    ws1.write(line, 23,((partner.membership_amount or 0.0) + ((partner.site_membership or 0) * unit_price)) * (1.0 + current_tax_rate))
                    ws1.write(line, 24, salesman and salesman.name or '')
                    ws1.write(line, 25, salesman and (salesman.phone or '') or '')
                    ws1.write(line, 26, salesman and (salesman.fax or '') or '')
                    ws1.write(line, 27, salesman and (salesman.mobile or '') or '')
                    ws1.write(line, 28, salesman and (salesman.email or '') or '')
                    ws1.write(line, 29, partner.membership_vcs or '')
                    ws1.write(line, 30, courtesy1)
                    ws1.write(line, 31, courtesy2)
                    line += 1
        wb1.save('calls.xls')
        result_file = open('calls.xls', 'rb').read()
        # give the result tos the user

        view = self.env.ref('cci_membership_extend.view_wizard_membership_calls_2_excel_msg_form')
        ctx = self.env.context.copy()
        ctx['msg'] = 'Save the File with '".xls"' extension.'
        ctx['file'] = base64.encodestring(result_file)
        return {
            'name': _('Result'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.membership.calls_2_excel.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx
        }


class wizard_membership_calls_2_excel_msg(models.TransientModel):
    _name = 'wizard.membership.calls_2_excel.msg'

    name = fields.Char(string='File name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    calls_xls = fields.Binary(string='Prepared file', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_membership_calls_2_excel_msg, self).default_get(fields)
        res['name'] = 'calls.xls'
        res['msg'] = self.env.context.get('msg')
        res['calls_xls'] = self.env.context.get('file')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

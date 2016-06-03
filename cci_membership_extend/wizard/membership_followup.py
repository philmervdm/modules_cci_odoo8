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
from openerp import api, fields, models, _
from openerp.exceptions import Warning
import base64
import datetime
from xlwt import *


class membership_followup(models.TransientModel):

    _name = 'membership.followup'

    year = fields.Integer(string='Current year', help='Year of the invoiced membership to follow-up',
                          required=True, default=datetime.datetime.today().year)
    address_type = fields.Selection([('default', 'Default address'),
                                     ('invoice', 'Invoice address otherwise defaut address'),
                                     ('contact_default', 'Membership Contact else default address'),
                                     ('contact_invoice', 'Membership Contact else invoice address otherwise defaut address')],
                                    default='invoice', string='Type of address')
    job_categs = fields.Char(string='Categories of searched contacts', size=20, required=True)
    limit_date = fields.Date(string='Limit Date', required=True)

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
    def extract_excel_file(self):
        # manage parameters
        if not self.year:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        if self.year and self.year < 1900:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        address_type = self.address_type
        if address_type[0:8] == 'contact_':
            if len(self.job_categs) > 0:
                membership_categ = self.job_categs[0]
            else:
                address_type = address_type[8:]  # we forget to search on membership categ because this is not given as parameters
        if len(self.job_categs) == 0:
            categs = 'G'
            len_categs = 1
        else:
            categs = self.job_categs
            len_categs = len(categs)
        # create empty sheet in excel file
        wb1 = Workbook()
        ws1 = wb1.add_sheet('Partners')
        ws1.write(0, 0, 'partner_id')
        ws1.write(0, 1, 'address_id')
        ws1.write(0, 2, 'job_id')
        ws1.write(0, 3, 'contact_id')
        ws1.write(0, 4, 'partner_last_invoice_id')
        ws1.write(0, 5, 'refuse_membership')
        ws1.write(0, 6, 'free_member')
        ws1.write(0, 7, 'associate_member')
        ws1.write(0, 8, 'domiciliation')
        ws1.write(0, 9, 'special_state')
        ws1.write(0, 10, 'partner_name')
        ws1.write(0, 11, 'street')
        ws1.write(0, 12, 'street2')
        ws1.write(0, 13, 'zip_code')
        ws1.write(0, 14, 'city')
        ws1.write(0, 15, 'phone_address')
        ws1.write(0, 16, 'fax_address')
        ws1.write(0, 17, 'email_address')
        ws1.write(0, 18, 'courtesy')
        ws1.write(0, 19, 'name')
        ws1.write(0, 20, 'first_name')
        ws1.write(0, 21, 'title')
        ws1.write(0, 22, 'title_categs')
        ws1.write(0, 23, 'email_contact')
        ws1.write(0, 24, 'phone_contact')
        ws1.write(0, 25, 'mobile_contact')
        ws1.write(0, 26, 'invoices_num')
        ws1.write(0, 27, 'invoices_count')
        ws1.write(0, 28, 'invoices_withtax_remaining')
        ws1.write(0, 29, 'vcs_last_invoice')
        ws1.write(0, 30, 'salesman')
        line = 1
        # prepare the inserting of new data
        PREFIXES = self.get_phone_country_prefix()
        # get the ids of account.journals of type 'sales'
        journal_obj = self.env['account.journal']
        sales_ids = journal_obj.search([('type', '=', 'sale')])
        # get this list of partners invoiced for the asked year of membership
        # even the inactive products
        # first, we extract all move concerned by theses products, then we check if these move are reconciled or not
        # then we extract the partener linked to move not reconciled event the partners not more invoicable
        # in an excel file providing special cases such as FREE MEMBER, ASSOCIATE MEMBER, REFUSE MEMBERSHIP, DOMICILED
        mprod_obj = self.env['product.product']
        mprod_ids = mprod_obj.search([('membership', '=', True),
                                      ('membership_year', '=', self.year),
                                      '|', ('active', '=', True), ('active', '=', False)])
        partner_ids = []
        move_ids = []
        if len(mprod_ids) > 0:
            selection = "SELECT distinct(move_id) \
                        FROM account_move_line \
                        WHERE product_id in (%s) \
                        AND date <= '%s' AND journal_id in (%s) \
                        AND reconcile_id IS NULL \
                        GROUP BY move_id" % (','.join([str(x) for x in mprod_ids.ids]), self.limit_date,
                                             ','.join([str(x) for x in sales_ids.ids]))
            self.env.cr.execute(selection)
            result = self.env.cr.fetchall()
            move_ids = [x[0] for x in result]
            moves = self.env['account.move'].browse(move_ids)
            acc_obj = self.env['account.account']
            acc_ids = acc_obj.search([('type', '=', 'receivable')])
            for move in moves:
                for mline in move.line_id:
                    if mline.account_id.id in acc_ids.ids:
                        if not mline.reconcile_id:
                            if move.partner_id and move.partner_id.id not in partner_ids:
                                partner_ids.append(move.partner_id.id)
                        break
        # extract all invoices concerned
        inv_obj = self.env['account.invoice']
        invoices = inv_obj.search([('move_id', 'in', move_ids)])
        # get all partners concerned
        partner_obj = self.env['res.partner']
        partners = partner_obj.browse(partner_ids)
        for partner in partners:
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
                #second (of first if contact_ if not asked), try to fin the first address of the good type
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
                global_name = ''
                if good_address.name and len(good_address.name) > 0:
                    if good_address.name[0:2] == '- ':
                        global_name = partner.name.strip() + ' ' + good_address.name.strip()
                    elif good_address.name[0:3] == ' - ':
                        global_name = partner.name.strip() + good_address.name.strip()
                    else:
                        global_name = good_address.name
                else:
                    global_name = partner.name
                # extract invoices data
                last_inv_id = 0
                inv_nums = []
                inv_count = 0
                inv_remaining = 0.0
                inv_last_vcs = ''
                for invoice in invoices:
                    if invoice.partner_id.id == partner.id:
                        inv_nums.append(invoice.number)
                        inv_count += 1
                        inv_remaining += invoice.residual
                        if invoice.id > last_inv_id:
                            last_inv_id = invoice.id
                            inv_last_vcs = invoice.name
                # record the data
                ws1.write(line, 0, partner.id)
                ws1.write(line, 1, good_address.id)
                ws1.write(line, 2, lFoundJob and sel_job.id or 0)
                ws1.write(line, 3, lFoundJob and sel_contact.id or 0)
                ws1.write(line, 4, last_inv_id)
                ws1.write(line, 5, partner.refuse_membership and 'REFUS' or '')
                ws1.write(line, 6, partner.free_member and 'GRATUIT' or '')
                ws1.write(line, 7, partner.associate_member and 'FILLEUL' or '')
                ws1.write(line, 8, partner.domiciliation and 'DOMICILIE' or '')
                ws1.write(line, 9, (partner.state_id and partner.state_id.id > 1) and partner.state_id.name or '')
                ws1.write(line, 10, global_name)
                ws1.write(line, 11, good_address.street or '')
                ws1.write(line, 12, good_address.street2 or '')
                ws1.write(line, 13, good_address.zip_id and good_address.zip_id.name or '')
                ws1.write(line, 14, good_address.zip_id and good_address.zip_id.city or '')
                ws1.write(line, 15, self.convert_phone(good_address.phone or '', PREFIXES))
                ws1.write(line, 16, self.convert_phone(good_address.fax or '', PREFIXES))
                ws1.write(line, 17, good_address.email or '')
                ws1.write(line, 18, lFoundJob and (sel_contact.title or '') or '')
                ws1.write(line, 19, lFoundJob and sel_contact.name or '')
                ws1.write(line, 20, lFoundJob and (sel_contact.first_name or '') or '')
                ws1.write(line, 21, lFoundJob and (sel_job.function_label or '') or '')
                ws1.write(line, 22, lFoundJob and sel_job.function_code_label or '')
                ws1.write(line, 23, selected_email)
                ws1.write(line, 24, self.convert_phone(lFoundJob and sel_job.phone or '', PREFIXES))
                ws1.write(line, 25, self.convert_phone(lFoundJob and sel_contact.mobile or '', PREFIXES))
                ws1.write(line, 26, ','.join(inv_nums))
                ws1.write(line, 27, inv_count)
                ws1.write(line, 28, inv_remaining)
                ws1.write(line, 29, inv_last_vcs)
                ws1.write(line, 30, partner.user_id and partner.user_id.name or '')
                line += 1
        wb1.save('membership_followup.xls')
        result_file = open('membership_followup.xls', 'rb').read()

        # give the result tos the user
        view = self.env.ref('cci_membership_extend.view_wizard_membership_followup_msg_form')
        ctx = self.env.context.copy()
        ctx['msg'] = 'Save the File with '".xls"' extension.'
        ctx['file'] = base64.encodestring(result_file)
        return {
            'name': _('Result'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.membership.followup.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx
        }


class wizard_membership_followup_msg(models.TransientModel):
    _name = 'wizard.membership.followup.msg'

    name = fields.Char(string='File name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    membership_followup_xls = fields.Binary(string='Prepared file', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_membership_followup_msg, self).default_get(fields)
        res['name'] = 'membership_followup.xls'
        res['msg'] = self.env.context.get('msg')
        res['membership_followup_xls'] = self.env.context.get('file')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

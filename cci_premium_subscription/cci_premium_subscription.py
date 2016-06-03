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
from openerp import models , fields , api , _
from openerp import tools
import datetime
import string
import re

CCIMAG_PRODUCT_CATEGORY = 7

def personalize_texts(self,subscription,tags,texts,renew_type=''):
    full_texts = []
    partner_obj = self.env['res.partner']
    for text in texts:
        for tag in tags.findall(text):
            tag_name = str(tag)
            if tag_name == '{PERSO sub_end_date}':
                text = text.replace(tag_name,subscription.end[8:10]+'/'+subscription.end[5:7]+'/'+subscription.end[0:4])
            elif tag_name == '{PERSO days_left}':
                if renew_type == 'RDPG2':
                    text = text.replace(tag_name,'7 jours')
                elif renew_type == 'RDPP2':
                    text = text.replace(tag_name,'7 jours')
                elif renew_type == 'RDPP3':
                    text = text.replace(tag_name,'15 jours')
                elif renew_type == 'MAGG1':
                    text = text.replace(tag_name,'15 jours')
                elif renew_type == 'MAGP2':
                    text = text.replace(tag_name,'1 mois')
                elif renew_type == 'MAGP3':
                    text = text.replace(tag_name,'15 jours')
                else:
                    text = text.replace(tag_name,'quelques')
            elif tag_name == '{PERSO contact_id}':
                text = text.replace(tag_name,subscription.contact_id and str(subscription.contact_id.id) or '0')
            elif tag_name == '{PERSO mag_end_date}':
                # 15 of month of last planned parution
                # 1. try to find the last used parution
                last_parution_date = '1980-01-01'
                for usage in subscription.usage_ids:
                    if usage.issue_id.issue_date and usage.issue_id.issue_date > last_parution_date:
                        last_parution_date = usage.issue_id.issue_date
                if last_parution_date == '1980-01-01':
                    last_parution_date = datetime.date.today().strftime('%Y-%m-%d')
                if subscription.left_usages > 0:
                    # extract the next 'x' parutions and order them by issue_date to keep the 'x' next one
                    sentence = "SELECT issue_date, name FROM sale_advertising_issue WHERE issue_date > '%s' and medium = %i ORDER BY issue_date ASC" % (last_parution_date,CCIMAG_PRODUCT_CATEGORY)
                    self.env.cr.execute(sentence)
                    res = self.env.cr.fetchall()
                    if len(res) >= subscription.left_usages:
                        mag_date = res[subscription.left_usages-1][0]
                    else:
                        mag_date = res[len(res)-1]
                else:
                    mag_date = last_parution_date[0:8]
                text = text.replace(tag_name,'15/'+mag_date[5:7]+'/'+mag_date[0:4])
            elif tag_name == '{PERSO salesman_coord}':
                salesman_coord = ''
                if subscription.partner_id and subscription.partner_id.user_id:
                    salesman_coord = subscription.partner_id.user_id.name
                    if subscription.partner_id.user_id.phone:
                        salesman_coord += u'<br/>Tél : ' + subscription.partner_id.user_id.phone
                    if subscription.partner_id.user_id.mobile:
                        salesman_coord += u'<br/>GSM : ' + subscription.partner_id.user_id.mobile
                else:
                    if subscription.contact_id and subscription.contact_id.other_contact_ids:
                        last_sequence = 9999
                        for job in subscription.contact_id.other_contact_ids:
                            if job.sequence_contact < last_sequence and job.address_id and job.address_id.parent_id and job.address_id.parent_id.user_id:
                                salesman_coord = job.address_id.parent_id.user_id.name
                                if job.address_id.parent_id.user_id.phone:
                                    salesman_coord += u'<br/>Tél : ' + job.address_id.parent_id.user_id.phone
                                if job.address_id.parent_id.user_id.mobile:
                                    salesman_coord += u'<br/>GSM : ' + job.address_id.parent_id.user_id.mobile
                                last_sequence = job.sequence_contact
                if not salesman_coord:
                    salesman_coord = 'Christophe Raymond<br/>Tél : 081/320.555<br/>GSM : 0476/75.32.59'
                text = text.replace(tag_name,salesman_coord)
        full_texts.append(text)
    return full_texts

def _check_digit_1_digit(digital_string):
    digit_sum = 0
    for carac in digital_string:
        if carac.isdigit():
            digit_sum += int(carac)
    return str(digit_sum)[-1:]

def _link_id(record_id):
    partner = str(record_id).rjust(5,'0')
    inv_partner = ''
    for carac in partner:
        inv_partner = carac + inv_partner
    year = (7 * int(inv_partner[3:4])) + int(inv_partner[2:3]) + 13 ## year was the last two caracters of the current year
    link_id = inv_partner[0:3] + str(year) + inv_partner[3:4]
    link_id += _check_digit_1_digit(link_id)
    link_id += inv_partner[4:5]
    rest = int(link_id) % 93
    link_id += _check_digit_1_digit(link_id)
    link_id = link_id + str(rest).rjust(2,'0')
    return link_id
    
def send_todo_renew_mail(subscription):
    return True
    
#class premium_subscription_type(models.Model):
#    _name = "premium_subscription.type"
#    _description = "Type/Group of Subscriptions"
#
#    name = fields.Char('Name',size=100,required=True)
#    code = fields.Char('Code',size=10)
#    product_ids = fields.One2many('product.product','premium_subscription_type_id','Linked Products')

#class product_product(models.Model):
#    _name = 'product.product'
#    _inherit = 'product.product'
#
#    premium_subscription_type_id = fields.Many2one('premium_subscription.type','Premium Subscription Type')

#class premium_subscription(models.Model):
#    _name = "premium_subscription"
#    _description = "Subscriptions for Premium Members"
#    
#    name = fields.Char('Description',size=100)
#    date = fields.Date('Date of subscription', default=fields.Date.today())
#    begin = fields.Date('Begin of Subscription', default=fields.Date.today())
#    end = fields.Date('End of Subscription')
#    invoice_id = fields.Many2one('account.invoice','Invoice')
#    contact_id = fields.Many2one('res.partner','Premium Member')
#    partner_id = fields.Many2one('res.partner','Partner (for invoice)')
#    type_id = fields.Many2one('premium_subscription.type','Type')
#    product_id = fields.Many2one('product.product','Product')
#    price = fields.Float('Price WoVAT',digits=(16, 2))
#    source = fields.Char('Source',size=30)
#    usages = fields.Integer('Usages')
#    left_usages = fields.Integer('Left Usages')
#    state = fields.Selection([('draft','Draft'),('current','Current'),('closed','Closed'),('cancel','Canceled')],default='draft', string='State')
#    close_date = fields.Date('Close Date')
#    close_user_id = fields.Many2one('res.users','Close User')
#    close_source = fields.Char('Source of Close',size=30)
#    specific_email = fields.Char('Specific EMail',size=250)
#    specific_name = fields.Char('Specific Name',size=120)
#    specific_street = fields.Char('Specific Street',size=120)
#    specific_street2 = fields.Char('Specific Street2',size=120)
#    specific_zip_id = fields.Many2one('res.partner.zip','Zip')
#    specific_country_id = fields.Many2one('res.country','Country')
#    usage_ids =  fields.One2many('premium_subscription.usage','subscription_id','Usages')
#    refuse_renew =  fields.Boolean('Refuse Renew')
#    active = fields.Boolean('Active', default=True)
#
#    _order = 'date desc'
#    
#    @api.onchange('product_id')
#    def _onchange_product_id(self):
#        if not self.product_id:
#            self.price = False
#            self.name = False
#        data_product = self.env['product.product'].browse(self.product_id.id)
#        if data_product:
#            self.name = data_product.name
#            self.price = data_product.list_price
#        else:
#            self.name = False
#            self.price = False
#    
#    @api.multi
#    def button_draft(self):
#        self.write({'state':'draft','close_date':False,'close_user_id':False,'close_source':''})
#        return True
#    @api.multi
#    def button_current(self):
#        self.write({'state':'current','close_date':False,'close_user_id':False,'close_source':''})
#        return True
#    @api.multi
#    def button_close(self):
#        self.write({'state':'closed','close_date':datetime.datetime.today().strftime('%Y-%m-%d'),'close_user_id':self.env.uid,'close_source':'Manual'})
#        return True
#    @api.multi
#    def button_cancel(self):
#        self.write({'state':'cancel','close_date':False,'close_user_id':False,'close_source':''})
#        return True
#    
#    @api.multi
#    def _create_new(self,contact_id,product_id,begin_date,partner_id,duration,first_issue_id,to_invoice):
#        msg_final = ''
#        new_id_sub = False
#        new_id_invoice = False
#
#        obj_sub = self.env['premium_subscription']
#        obj_product = self.env['product.product']
#        product = obj_product.browse(product_id)
#        data_sub = {}
#        data_sub['name'] = product.name
#        data_sub['date'] = datetime.datetime.today().strftime('%Y-%m-%d')
#        data_sub['begin'] = begin_date
#        end_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d") + datetime.timedelta(days=364)
#        data_sub['end'] = end_date.strftime('%Y-%m-%d')
#        data_sub['contact_id'] = contact_id
#        data_sub['partner_id'] = partner_id
#        data_sub['product_id'] = product.id
#        data_sub['price'] = product.list_price
#        data_sub['source'] = 'Manual wizard'
#        data_sub['usages'] = 10
#        data_sub['left_usages'] = 10
##         data_product = self.env['product.product'].browse(product_id)
#        data_sub['type_id'] = product.premium_subscription_type_id.id
#        data_usage = {}
#        if first_issue_id:
#            issue = self.env['sale.advertising.issue'].browse(first_issue_id)
#            contact = self.env['res.partner'].browse(contact_id)
#            contact = contact.read(['name','first_name'])[0]
#            data_usage['name'] = '%s pour %s %s' % (issue.name or '', contact['name'], contact['first_name'] or '')
#            data_usage['issue_id'] = first_issue_id
#            data_sub['left_usages'] += -1
#        data_sub['state'] = 'current'
#        if to_invoice and partner_id and data_sub['price'] > 0.0:
#            data_sub['invoice_id'] = False
#            obj_lines = self.env['account.invoice.line']
#            tax_ids=[]
#            val_invoice = self.env['account.invoice'].onchange_partner_id('out_invoice', partner_id)
#            val_invoice['value'].update({'partner_id': partner_id})
##             partner_address_id = val_invoice['value']['address_invoice_id']
##             if not partner_address_id:
##                 msg_final = "Given partner doesn't have an address to make the invoice.\nInvoice not generated but subscription created"
##             else:
#            obj_partner = self.env['res.partner']
#            partner = obj_partner.browse(partner_id)
#            value = obj_lines.product_id_change(product_id,uom_id =False, partner_id=partner_id, fposition_id=partner.property_account_position.id)
#            for tax in product.taxes_id:
#                tax_ids.append(tax.id)
#
#            vals = value['value']
#            c_name = product.name or ''
#            vals.update({
#                'name': c_name,
#                'price_unit': product.list_price,
#                'quantity': 1,
#                'product_id': product.id,
#                'invoice_line_tax_id': [(6,0,tax_ids)],
#            })
#            inv_line_ids = obj_lines.create(vals)
#            val_invoice['value'].update({
#                'origin': '',
#                'reference': False,
#                'invoice_line': [(6,0,inv_line_ids.ids)],
#                'comment': "",
#            })
#
#            inv_obj = self.env['account.invoice']
#            new_id_invoice = inv_obj.create(val_invoice['value'])
#            data_sub['invoice_id'] = new_id_invoice.id
#        else:
#            data_sub['invoice_id'] = False
#            
#        new_id_sub = obj_sub.create(data_sub)
#        
#        if data_usage:
#            data_usage['subscription_id'] = new_id_sub.id
#            self.env['premium_subscription.usage'].create(data_usage)
#        return (new_id_sub.id,new_id_invoice and new_id_invoice.id or False,msg_final)
#    
#    @api.multi
#    def _create_new_rdp(self,contact_id,product_id,begin_date,partner_id,duration,to_invoice,email):
#        msg_final = ''
#        new_id_sub = False
#        new_id_invoice = False
#
#        obj_sub = self.env['premium_subscription']
#        obj_product = self.env['product.product']
#        product = obj_product.browse(product_id)
#        data_sub = {}
#        data_sub['name'] = product.name
#        data_sub['date'] = datetime.datetime.today().strftime('%Y-%m-%d')
#        data_sub['begin'] = begin_date
#        end_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d") + datetime.timedelta(days=364)
#        data_sub['end'] = end_date.strftime('%Y-%m-%d')
#        data_sub['contact_id'] = contact_id
#        data_sub['partner_id'] = partner_id
#        data_sub['product_id'] = product.id
#        data_sub['price'] = product.list_price
#        data_sub['source'] = 'Manual wizard'
#        data_product = self.env['product.product'].browse(product_id)
#        data_sub['type_id'] = data_product.premium_subscription_type_id.id
#        data_sub['state'] = 'current'
#        if to_invoice and partner_id and data_sub['price']:
#            data_sub['invoice_id'] = False
#            obj_lines = self.env['account.invoice.line']
#            tax_ids=[]
#            val_invoice = self.env['account.invoice'].onchange_partner_id(type='out_invoice', partner_id=partner_id)
#            val_invoice['value'].update({'partner_id': partner_id})
#             partner_address_id = val_invoice['value']['address_invoice_id']
#             if not partner_address_id:
#                 msg_final = "Given partner doesn't have an address to make the invoice.\nInvoice not generated but subscription created"
#             else:
#            obj_partner = self.env['res.partner']
#            partner = obj_partner.browse(partner_id)
#            value = obj_lines.product_id_change(product=product_id,uom_id =False, partner_id=partner_id, fposition_id=partner.property_account_position.id)
#            for tax in data_product.taxes_id:
#                tax_ids.append(tax.id)
#
#            vals = value['value']
#            c_name = data_product.name or ''
#            vals.update({
#                'name': c_name,
#                'price_unit': data_product.list_price,
#                'quantity': 1,
#                'product_id': data_product.id,
#                'invoice_line_tax_id': [(6,0,tax_ids)],
#            })
#            inv_line_ids = obj_lines.create(vals)
#            val_invoice['value'].update({
#                'origin': '',
#                'reference': False,
#                'invoice_line': [(6,0,inv_line_ids.ids)],
#                'comment': "",
#            })
#
#            inv_obj = self.env['account.invoice']
#            new_id_invoice = inv_obj.create(val_invoice['value'])
#            data_sub['invoice_id'] = new_id_invoice.id
#        else:
#            data_sub['invoice_id'] = False
#        
#        new_id_sub = obj_sub.create(data_sub)
#        
#        return (new_id_sub.id,new_id_invoice and new_id_invoice.id or False,msg_final)
#    
#    @api.multi
#    def _create_new_full_page(self,contact_id,product_id,begin_date,partner_id,forced_end_date,to_invoice):
#        msg_final = ''
#        new_id_sub = False
#        new_id_invoice = False
#
#        obj_sub = self.env['premium_subscription']
#        obj_product = self.env['product.product']
#        product = obj_product.browse(product_id)
#        data_sub = {}
#        data_sub['name'] = product.name
#        data_sub['date'] = datetime.datetime.today().strftime('%Y-%m-%d')
#        data_sub['begin'] = begin_date
#        data_sub['end'] = forced_end_date
#        data_sub['contact_id'] = contact_id
#        data_sub['partner_id'] = partner_id
#        data_sub['product_id'] = product.id
#        data_sub['price'] = product.list_price
#        data_sub['source'] = 'Manual wizard'
##         data_product = self.pool.get('product.product').browse(cr,uid,product_id)
#        data_sub['type_id'] = product.premium_subscription_type_id.id
#        data_sub['state'] = 'current'
#        if to_invoice and partner_id and data_sub['price']:
#            data_sub['invoice_id'] = False
#            obj_lines = self.env['account.invoice.line']
#            tax_ids=[]
#            val_invoice = self.env['account.invoice'].onchange_partner_id('out_invoice', partner_id)
#            val_invoice['value'].update({'partner_id': partner_id})
#
##             partner_address_id = val_invoice['value']['address_invoice_id']
##             if not partner_address_id:
##                 msg_final = "Given partner doesn't have an address to make the invoice.\nInvoice not generated but subscription created"
##             else:
#            obj_partner = self.env['res.partner']
#            partner = obj_partner.browse(partner_id)
#            value = obj_lines.product_id_change(product_id,uom_id =False, partner_id=partner_id, fposition_id=partner.property_account_position.id)
#            for tax in product.taxes_id:
#                tax_ids.append(tax.id)
#
#            vals = value['value']
#            c_name = product.name or ''
#            vals.update({
#                'name': c_name,
#
#                'price_unit': product.list_price,
#                'quantity': 1,
#                'product_id': product.id,
#                'invoice_line_tax_id': [(6,0,tax_ids)],
#            })
#            inv_line_ids = obj_lines.create(vals)
#            val_invoice['value'].update({
#                'origin': '',
#                'reference': False,
#                'invoice_line': [(6,0,inv_line_ids.ids)],
#                'comment': "",
#            })
#
#            inv_obj = self.env['account.invoice']
#            new_id_invoice = inv_obj.create(val_invoice['value'])
#            data_sub['invoice_id'] = new_id_invoice.id
#        else:
#            data_sub['invoice_id'] = False
#            
#        new_id_sub = obj_sub.create(data_sub)
#        
#        return (new_id_sub.id,new_id_invoice and new_id_invoice.id or False,msg_final)
#    
#    @api.multi
#    def _send_url(self,subscription_id,template_id,forced_address):
#        template_obj = self.env['email.template']
#        template = template_obj.browse(template_id)
#        sub_obj = self.env['premium_subscription']
#        subscription = sub_obj.browse(subscription_id)
#        final_email = ''
#        if forced_address:
#            final_email = forced_address
#        elif subscription.contact_id and subscription.contact_id.email:
#            final_email = subscription.contact_id.email
#        elif subscription.contact_id and subscription.contact_id.other_contact_ids:
#            min_sequence = 9999
#            for current_job in subscription.contact_id.other_contact_ids:
#                if current_job.email and current_job.sequence_contact < min_sequence:
#                    min_sequence = current_job.sequence_contact
#                    final_email = current_job.email
#        if final_email:
#            courtesy = subscription.contact_id.title
#            name = subscription.contact_id.name
#            email_content = template.body_html.replace('[courtesy]',courtesy).replace('[name]',name)
#            if subscription.begin:
#                email_content = email_content.replace('[from]',subscription.begin[8:10]+'/'+subscription.begin[5:7]+'/'+subscription.begin[0:4])
#            else:
#                email_content = email_content.replace('[from]','')
#            if subscription.end:
#                email_content = email_content.replace('[to]',subscription.end[8:10]+'/'+subscription.end[5:7]+'/'+subscription.end[0:4])
#            else:
#                email_content = email_content.replace('[to]','')
#            
#            if subscription.contact_id and subscription.contact_id.other_contact_ids:
#                links = []
#                for current_job in subscription.contact_id.other_contact_ids:
#                    if current_job.address_id and not current_job.address_id.dir_exclude and current_job.address_id.active and current_job.address_id.partner_id \
#                           and current_job.address_id.partner_id.active and current_job.address_id.partner_id.state_id and current_job.address_id.partner_id.state_id.id == 1:
#                        links.append( _link_id(subscription.contact_id.id ) )
#                if not links:
#                    final_email = ''
#            else:
#                final_email = ''
#            
#            if final_email:
#                full_links = []
#                for link in links:
#                    full_links.append( '<a href="http://www.ccilvn.be/mise-a-jour-repertoire/?key=%s">http://www.ccilvn.be/mise-a-jour-repertoire/?key=%s</a>' % (link,link) )
#                inside = u'</li><li>'.join(full_links)
#                email_content = email_content.replace('[links]',u'<ul><li>' + inside + u'</li></ul>')
#                errors = []
#                try:
#                    tools.email_send('fb@ccilvn.be', [final_email,], template.subject or '', email_content, subtype=template.type)
#                except:
#                    errors.append(email_address)
#                if errors:
#                    final_email = ''
#        return (final_email)
#    
#    @api.multi
#    def _send_renew_messages(self):
#        ''' 
#        This method detects subscription to be renewed in next days.
#        And send messages to subcribers to make them renew
#        To prevent errors if server doesn't work some days, we record each sending
#        and try to make the same sending during three days : the good one and the two days following
#        '''
#        # Start log
##         cronline_id = self.pool.get('cci_logs.cron_line')._start(cr,uid,'RenewPremiumSubscriptions')
#        final_result = True
#        parameter_obj = self.env('ir.config_parameter')
#        template_obj = self.env['email_template']
#        tags = re.compile('{PERSO .*?}',re.IGNORECASE)
#        #
#        # 1. Renew free subscription to revue de presse
#        # 1.A. First call
##         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'1A. First call to renew free press review\n\n')
#        today5 = datetime.date.today() + datetime.timedelta(days=5)
#        today7 = datetime.date.today() + datetime.timedelta(days=7)
#        type_obj = self.env['premium_subscription.type']
#        type_ids = type_obj.search([('code','=','RDP')])
#        if type_ids:
#            param_values = self.env['ir.config_parameter'].get_param('PremiumRenewRDPG1')
#            if param_values:
#                templates = template_obj.search([('name','=',param_values)])
#                if templates:
#                    template = templates[0]
#                    sub_obj = self.env['premium_subscription']
#                    free_to_renew_call1_ids = sub_obj.search([('end','>=',today5),('end','<=',today7),('state','=','current'),('refuse_renew','=',False),('type_id','in',type_ids),('price','>',-0.01),('price','<',0.01)])
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'%i subscriptions to check\n' % len(free_to_renew_call1_ids))
#                    if free_to_renew_call1_ids:
#                        renew_obj = self.env['premium_subscription.renew']
#                        subs = free_to_renew_call1_ids
#                        already_renewed = 0
#                        done_renewals = 0
#                        no_email = []
#                        sended = []
#                        for sub in subs:
#                            # search if new subscription for press review already exists in the future for this contact_id
#                            existing_sub_ids = sub_obj.search([('contact_id','=',sub.contact_id.id),('type_id','in',type_ids),('end','>',sub.end),('state','in',['current','draft'])])
#                            if not existing_sub_ids:
#                                renew_ids = renew_obj.search([('subscription_id','=',sub.id),('type','=','RDPG1')])
#                                if not renew_ids: # if renew_ids, this subscription has already been send to renew
#                                    email_address = False
#                                    if sub.specific_email:
#                                        email_address = sub.specific_email
#                                    else: # Needs to be FIX
#                                        # search for email address to use
#                                        if sub.contact_id and sub.parent_id and sub.contact_id.other_contact_ids:
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id and job.email:
#                                                    email_address = job.email
#                                        if (not email_address) and sub.contact_id and sub.contact_id.email:
#                                            email_address = sub.contact_id.email
#                                        elif (not email_address) and sub.contact_id and sub.contact_id.job_email:
#                                            email_address = sub.contact_id.job_email
#                                        if not email_address and sub.contact_id and sub.contact_id.other_contact_ids:
#                                            min_sequence = 999
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.email and job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id:
#                                                    if job.sequence_contact < min_sequence:
#                                                        email_address = job.email
#                                                        min_sequence = job.sequence_contact
#                                    if email_address:
#                                        full_texts = personalize_texts(self,sub,tags,[template.subject,template.body],'RDPG1')
#                                        # sending of the email
#                                        tools.email_send('abonnements@ccilvn.be', [email_address,], full_texts[0], full_texts[1], subtype=template.type)
#                                        #tools.email_send('abonnements@ccilvn.be', ['philmer.vdm@gmail.com',], full_texts[0], full_texts[1], subtype=template.type)
#                                        #
#                                        sended.append(email_address)
#                                        renew_obj.create({'name':'Premier appel renouvellement Revue de Presse gratuite','subscription_id':sub.id,'date':datetime.date.today().strftime('%Y-%m-%d'),'email':email_address,'type':'RDPG1'})
#                                    else:
#                                        no_email.append(sub.id)
#                                        final_result = False
#                                        send_todo_renew_mail(sub)
##                                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview [subscriptionID %i]: no email address found\n' % sub.id)
#                                else:
#                                    done_renewals += 1
#                            else:
#                                already_renewed += 1
##                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Results :\nSended Emails : %s\nNo Email Subscription IDS : %s\nAlready Renewed : %i\nAlready sended Renewals : %i' % (
##                                                                                                                                 sended and (','.join(sended)) or '-/-',
##                                                                                                                                 no_email and (','.join([str(x) for x in no_email])) or '-/-',
##                                                                                                                                 already_renewed,
##                                                                                                                                 done_renewals,))
#                else:
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview : Wrong Template ID\n')
#                    final_result = False
#            else:
##                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview : No Template\n')
#                final_result = False
#        else:
##             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview : type unfound\n')
#            final_result = False
#        # 1.B. First (and last in the same time) recall
##         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\n\n1B. First (and last) recall to renew free press review\n\n')
#        today1 = datetime.date.today() + datetime.timedelta(days=1)
#        today = datetime.date.today()
#        type_obj = self.env['premium_subscription.type']
#        type_ids = type_obj.search([('code','=','RDP')])
#        if type_ids:
#            param_values = self.env['ir.config_parameter'].get_param('PremiumRenewRDPG2')
#            if param_values:
#                templates = template_obj.search([('name','=',param_values)])
#                if templates:
#                    template = templates[0]
#                    sub_obj = self.env['premium_subscription']
#                    free_to_renew_recall1_ids = sub_obj.search([('end','>=',today),('end','<=',today1),('state','=','current'),('refuse_renew','=',False),('type_id','in',type_ids),('price','>',-0.01),('price','<',0.01)])
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'%i subscriptions to check\n' % len(free_to_renew_recall1_ids))
#                    if free_to_renew_recall1_ids:
#                        renew_obj = self.pool.get('premium_subscription.renew')
#                        subs = free_to_renew_recall1_ids #sub_obj.browse(cr,uid,free_to_renew_recall1_ids)
#                        already_renewed = 0
#                        done_renewals = 0
#                        no_email = []
#                        sended = []
#                        for sub in subs:
#                            # search if new subscription for press review already exists in the future for this contact_id
#                            existing_sub_ids = sub_obj.search([('contact_id','=',sub.contact_id.id),('type_id','in',type_ids),('end','>',sub.end),('state','in',['current','draft'])])
#                            if not existing_sub_ids:
#                                renew_ids = renew_obj.search([('subscription_id','=',sub.id),('type','=','RDPG2')])
#                                if not renew_ids: # if renew_ids, this subscription has already been send to renew
#                                    email_address = False
#                                    if sub.specific_email:
#                                        email_address = sub.specific_email
#                                    else: # Needs to be FIX
#                                        # search for email address to use
#                                        if sub.contact_id and sub.parent_id and sub.contact_id.other_contact_ids:
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id and job.email:
#                                                    email_address = job.email
#                                        if (not email_address) and sub.contact_id and sub.contact_id.email:
#                                            email_address = sub.contact_id.email
#                                        elif (not email_address) and sub.contact_id and sub.contact_id.job_email:
#                                            email_address = sub.contact_id.job_email
#                                        if not email_address and sub.contact_id and sub.contact_id.other_contact_ids:
#                                            min_sequence = 999
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.email and job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id:
#                                                    if job.sequence_contact < min_sequence:
#                                                        email_address = job.email
#                                                        min_sequence = job.sequence_contact
#                                    if email_address:
#                                        full_texts = personalize_texts(self,sub,tags,[template.subject,template.body],'RDPG2')
#                                        # sending of the email
#                                        tools.email_send('abonnements@ccilvn.be', [email_address,], full_texts[0], full_texts[1], subtype=template.type)
#                                        #tools.email_send('abonnements@ccilvn.be', ['philmer.vdm@gmail.com',], full_texts[0], full_texts[1], subtype=template.type)
#                                        sended.append(email_address)
#                                        renew_obj.create({'name':'Rappel renouvellement Revue de Presse gratuite','subscription_id':sub.id,'date':datetime.date.today().strftime('%Y-%m-%d'),'email':email_address,'type':'RDPG2'})
#                                    else:
#                                        no_email.append(sub.id)
#                                        final_result = False
#                                        send_todo_renew_mail(sub)
##                                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview [subscriptionID %i]: no email address found\n' % sub.id)
#                                else:
#                                    done_renewals += 1
#                            else:
#                                already_renewed += 1
##                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Results :\nSended Emails : %s\nNo Email Subscription IDS : %s\nAlready Renewed : %i\nAlready sended Renewals : %i' % (
##                                                                                                                                 sended and (','.join(sended)) or '-/-',
##                                                                                                                                 no_email and (','.join([str(x) for x in no_email])) or '-/-',
##                                                                                                                                 already_renewed,
##                                                                                                                                 done_renewals,))
#                else:
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview : Wrong Template ID\n')
#                    final_result = False
#            else:
##                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview : No Template\n')
#                final_result = False
#        else:
##             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free PressReview : type unfound\n')
#
#            final_result = False
#        # 2. Renew paid subscription to revue de presse
#        # 2.A. First call
##         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\n\n2A. First call to renew paid press review\n\n')
#        today12 = datetime.date.today() + datetime.timedelta(days=12)
#        today14 = datetime.date.today() + datetime.timedelta(days=14)
#        type_obj = self.env['premium_subscription.type']
#        type_ids = type_obj.search([('code','=','RDP')])
#        if type_ids:
#            param_values = self.env['ir.config_parameter'].get_param('PremiumRenewRDPP1')
#            if param_values:
#                templates = template_obj.search([('name','=',param_values)])
#                if templates:
#                    template = templates[0]
#                    sub_obj = self.env['premium_subscription']
#                    paid_to_renew_call1_ids = sub_obj.search([('end','>=',today12),('end','<=',today14),('state','=','current'),('refuse_renew','=',False),('type_id','in',type_ids),('price','>=',0.01)])
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'%i subscriptions to check\n' % len(paid_to_renew_call1_ids))
#                    if paid_to_renew_call1_ids:
#                        renew_obj = self.env['premium_subscription.renew']
#                        subs = paid_to_renew_call1_ids #sub_obj.browse(paid_to_renew_call1_ids)
#                        already_renewed = 0
#                        done_renewals = 0
#                        no_email = []
#                        sended = []
#                        for sub in subs:
#                            # search if new subscription for press review already exists in the future for this contact_id
#                            existing_sub_ids = sub_obj.search([('contact_id','=',sub.contact_id.id),('type_id','in',type_ids),('end','>',sub.end),('state','in',['current','draft'])])
#                            if not existing_sub_ids:
#                                renew_ids = renew_obj.search([('subscription_id','=',sub.id),('type','=','RDPP1')])
#                                if not renew_ids: # if renew_ids, this subscription has already been send to renew
#                                    email_address = False
#                                    if sub.specific_email:
#                                        email_address = sub.specific_email
#                                    else: # To be Fix
#                                        # search for email address to use
#                                        if sub.contact_id and sub.partner_id and sub.contact_id.other_contact_ids:
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id and job.email:
#                                                    email_address = job.email
#                                        if (not email_address) and sub.contact_id and sub.contact_id.email:
#                                            email_address = sub.contact_id.email
#                                        elif (not email_address) and sub.contact_id and sub.contact_id.job_email:
#                                            email_address = sub.contact_id.job_email
#                                        if not email_address and sub.contact_id and sub.contact_id.other_contact_ids:
#                                            min_sequence = 999
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.email and job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id:
#                                                    if job.sequence_contact < min_sequence:
#                                                        email_address = job.email
#                                                        min_sequence = job.sequence_contact
#                                    if email_address:
#                                        full_texts = personalize_texts(self,sub,tags,[template.subject,template.body],'RDPP1')
#                                        # sending of the email
#                                        tools.email_send('abonnements@ccilvn.be', [email_address,], full_texts[0], full_texts[1], subtype=template.type)
#                                        #tools.email_send('abonnements@ccilvn.be', ['philmer.vdm@gmail.com',], full_texts[0], full_texts[1], subtype=template.type)
#                                        #
#                                        sended.append(email_address)
#                                        renew_obj.create({'name':'Premier appel renouvellement Revue de Presse payante','subscription_id':sub.id,'date':datetime.date.today().strftime('%Y-%m-%d'),'email':email_address,'type':'RDPP1'})
#                                    else:
#                                        no_email.append(sub.id)
#                                        final_result = False
#                                        send_todo_renew_mail(sub)
##                                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview [subscriptionID %i]: no email address found\n' % sub.id)
#                                else:
#                                    done_renewals += 1
#                            else:
#                                already_renewed += 1
##                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Results :\nSended Emails : %s\nNo Email Subscription IDS : %s\nAlready Renewed : %i\nAlready sended Renewals : %i' % (
##                                                                                                                                 sended and (','.join(sended)) or '-/-',
##                                                                                                                                 no_email and (','.join([str(x) for x in no_email])) or '-/-',
##                                                                                                                                 already_renewed,
##                                                                                                                                 done_renewals,))
#               else:
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : Wrong Template ID\n')
#                    final_result = False
#            else:
##                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : No Template\n')
#                final_result = False
#        else:
##             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : type unfound\n')
#            final_result = False
#        # 2.B. First (and last in the same time) recall
##         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\n\n2B. First recall to renew paid press review\n\n')
#        today5 = datetime.date.today() + datetime.timedelta(days=5)
#        today7 = datetime.date.today() + datetime.timedelta(days=7)
#        type_obj = self.env['premium_subscription.type']
#        type_ids = type_obj.search([('code','=','RDP')])
#        if type_ids:
#            param_values = self.env['ir.config_parameter'].get_param('PremiumRenewRDPG2')
#            if param_values:
#                templates = template_obj.search([('name','=',templates)])
#                if templates:
#                    template = templates[0]
#                    sub_obj = self.env['premium_subscription']
#                    paid_to_renew_recall1_ids = sub_obj.search([('end','>=',today5),('end','<=',today7),('state','=','current'),('refuse_renew','=',False),('type_id','in',type_ids),('price','>=',0.01)])
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'%i subscriptions to check\n' % len(paid_to_renew_recall1_ids))
#                    if paid_to_renew_recall1_ids:
#                        renew_obj = self.env['premium_subscription.renew']
#                        subs = paid_to_renew_recall1_ids #sub_obj.browse(cr,uid,paid_to_renew_recall1_ids)
#                        already_renewed = 0
#                        done_renewals = 0
#                        no_email = []
#                        sended = []
#                        for sub in subs:
#                            # search if new subscription for press review already exists in the future for this contact_id
#                            existing_sub_ids = sub_obj.search([('contact_id','=',sub.contact_id.id),('type_id','in',type_ids),('end','>',sub.end),('state','in',['current','draft'])])
#                            if not existing_sub_ids:
#                                renew_ids = renew_obj.search([('subscription_id','=',sub.id),('type','=','RDPP2')])
#                                if not renew_ids: # if renew_ids, this subscription has already been send to renew
#                                    email_address = False
#                                    if sub.specific_email:
#                                        email_address = sub.specific_email
#                                    else: # To be Fixed
#                                        # search for email address to use
#                                        if sub.contact_id and sub.partner_id and sub.contact_id.other_contact_ids:
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id and job.email:
#                                                    email_address = job.email
#                                        if (not email_address) and sub.contact_id and sub.contact_id.email:
#                                            email_address = sub.contact_id.email
#                                        elif (not email_address) and sub.contact_id and sub.contact_id.job_email:
#                                            email_address = sub.contact_id.job_email
#                                        if not email_address and sub.contact_id and sub.contact_id.other_contact_ids:
#                                            min_sequence = 999
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.email and job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id:
#                                                    if job.sequence_contact < min_sequence:
#                                                        email_address = job.email
#                                                        min_sequence = job.sequence_contact
#                                    if email_address:
#                                        full_texts = personalize_texts(self,sub,tags,[template.subject,template.body],'RDPP2')
#                                        # sending of the email
#                                        tools.email_send('abonnements@ccilvn.be', [email_address,], full_texts[0], full_texts[1], subtype=template.type)
#                                        #tools.email_send('abonnements@ccilvn.be', ['philmer.vdm@gmail.com',], full_texts[0], full_texts[1], subtype=template.type)
#                                        sended.append(email_address)
#                                        renew_obj.create({'name':'Premier Rappel renouvellement Revue de Presse payante','subscription_id':sub.id,'date':datetime.date.today().strftime('%Y-%m-%d'),'email':email_address,'type':'RDPP2'})
#                                    else:
#                                        no_email.append(sub.id)
#                                        final_result = False
#                                        send_todo_renew_mail(sub)
##                                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview [subscriptionID %i]: no email address found\n' % sub.id)
#                                else:
#                                    done_renewals += 1
#                            else:
#                                already_renewed += 1
##                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Results :\nSended Emails : %s\nNo Email Subscription IDS : %s\nAlready Renewed : %i\nAlready sended Renewals : %i' % (
##                                                                                                                                 sended and (','.join(sended)) or '-/-',
##                                                                                                                                 no_email and (','.join([str(x) for x in no_email])) or '-/-',
##                                                                                                                                 already_renewed,
##                                                                                                                                 done_renewals,))
#                else:
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : Wrong Template ID\n')
#                    final_result = False
#            else:
##                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : No Template\n')
#                final_result = False
#        else:
##             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : type unfound\n')
#            final_result = False
#        # 2.C. Second (and last in the same time) recall
##         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\n\n2C. Second recall to renew paid press review\n\n')
#        today1 = datetime.date.today() + datetime.timedelta(days=1)
#        today = datetime.date.today()
#        type_obj = self.env['premium_subscription.type']
#        type_ids = type_obj.search([('code','=','RDP')])
#        if type_ids:
#            param_values = self.env['ir.config_parameter'].get_param('PremiumRenewRDPP3')
#            if param_values:
#                templates = template_obj.search([('name','=',param_values)])
#                if templates:
#                    template = templates[0]
#                    sub_obj = self.env['premium_subscription']
#                    paid_to_renew_recall2_ids = sub_obj.search([('end','>=',today),('end','<=',today1),('state','=','current'),('refuse_renew','=',False),('type_id','in',type_ids),('price','>=',0.01)])
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'%i subscriptions to check\n' % len(paid_to_renew_recall2_ids))
#                    if paid_to_renew_recall2_ids:
#                        renew_obj = self.env['premium_subscription.renew']
#                        subs = paid_to_renew_recall2_ids #sub_obj.browse(cr,uid,paid_to_renew_recall2_ids)
#                        already_renewed = 0
#                        done_renewals = 0
#                        no_email = []
#                        sended = []
#                        for sub in subs:
#                            # search if new subscription for press review already exists in the future for this contact_id
#                            existing_sub_ids = sub_obj.search([('contact_id','=',sub.contact_id.id),('type_id','in',type_ids),('end','>',sub.end),('state','in',['current','draft'])])
#                            if not existing_sub_ids:
#                                renew_ids = renew_obj.search([('subscription_id','=',sub.id),('type','=','RDPP3')])
#                                if not renew_ids: # if renew_ids, this subscription has already been send to renew
#                                    email_address = False
#                                    if sub.specific_email:
#                                        email_address = sub.specific_email
#                                    else: # To be Fixed
#                                        # search for email address to use
#                                        if sub.contact_id and sub.partner_id and sub.contact_id.other_contact_ids:
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id and job.email:
#                                                    email_address = job.email
#                                        if (not email_address) and sub.contact_id and sub.contact_id.email:
#                                            email_address = sub.contact_id.email
#                                        elif (not email_address) and sub.contact_id and sub.contact_id.job_email:
#                                            email_address = sub.contact_id.job_email
#                                        if not email_address and sub.contact_id and sub.contact_id.other_contact_ids:
#                                            min_sequence = 999
#                                            for job in sub.contact_id.other_contact_ids:
#                                                if job.email and job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id:
#                                                    if job.sequence_contact < min_sequence:
#                                                        email_address = job.email
#                                                        min_sequence = job.sequence_contact
#                                    if email_address:
#                                        full_texts = personalize_texts(self,sub,tags,[template.subject,template.body],'RDPP3')
#                                        # sending of the email
#                                        tools.email_send('abonnements@ccilvn.be', [email_address,], full_texts[0], full_texts[1], subtype=template.type)
#                                        #tools.email_send('abonnements@ccilvn.be', ['philmer.vdm@gmail.com',], full_texts[0], full_texts[1], subtype=template.type)
#                                        sended.append(email_address)
#                                        renew_obj.create({'name':'Second Rappel renouvellement Revue de Presse payante','subscription_id':sub.id,'date':datetime.date.today().strftime('%Y-%m-%d'),'email':email_address,'type':'RDPP3'})
#                                    else:
#                                        no_email.append(sub.id)
#                                        final_result = False
#                                        send_todo_renew_mail(sub)
##                                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview [subscriptionID %i]: no email address found\n' % sub.id)
#                                else:
#                                    done_renewals += 1
#                            else:
#                                already_renewed += 1
##                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Results :\nSended Emails : %s\nNo Email Subscription IDS : %s\nAlready Renewed : %i\nAlready sended Renewals : %i' % (
##                                                                                                                                 sended and (','.join(sended)) or '-/-',
##                                                                                                                                 no_email and (','.join([str(x) for x in no_email])) or '-/-',
##                                                                                                                                 already_renewed,
##                                                                                                                                 done_renewals,))
#                else:
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : Wrong Template ID\n')
#                    final_result = False
#            else:
##                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : No Template\n')
#                final_result = False
#        else:
##             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Paid PressReview : type unfound\n')
#            final_result = False
#        #
#        # 3. Renews free subscription to CCI Mag
#        today = datetime.date.today().strftime('%Y-%m-%d')
#        sub_obj = self.env['premium_subscription']
#        for spec in [{'day':'01','type':'MAGG1','name':u'\n\n3A. First call to renew free CCI Mag\n\n','renew_name':u'Premier appel renouvellement CCI Mag gratuit','left':0},
#                     {'day':'15','type':'MAGG2','name':u'\n\n3B. First Recall to renew free CCI Mag\n\n','renew_name':u'Premier et unique Rappel renouvellement CCI Mag gratuit','left':0},
#                     {'day':'01','type':'MAGP1','name':u'\n\n4A. First call to renew paid CCI Mag\n\n','renew_name':u'Premier appel renouvellement CCI Mag payant','left':1},
#                     {'day':'01','type':'MAGP2','name':u'\n\n4B. First Recall to renew paid CCI Mag\n\n','renew_name':u'Premier et unique Rappel renouvellement CCI Mag payant','left':0},
#                     {'day':'15','type':'MAGP3','name':u'\n\n4C. Second Recall to renew paid CCI Mag\n\n','renew_name':u'Second Rappel renouvellement CCI Mag payant','left':0},]:
#            if today[8:10] == spec['day']:
##                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,spec['name'])
#                
#                # select all free subscription in state 'closed' with a usage in the same month
#                sentence = """SELECT subscription_id FROM premium_subscription_usage
#                                  WHERE issue_id IN (SELECT id FROM sale_advertising_issue 
#                                                         WHERE medium = 7 and issue_date >= '%s' and issue_date <= '%s')
#                           """ % (today[0:8]+'01', today[0:8]+'28')
#                self.env.cr.execute(sentence)
#                res = self.env.cr.fetchall()
#                if res:
#                    this_month_used_sub_ids = [x[0] for x in res]
#                    type_obj = self.env['premium_subscription.type']
#                    type_ids = type_obj.search([('code','=','CCIMAG')])
#                    if type_ids:
#                        param_values = self.env['ir.config_parameter'].get_param('PremiumRenew'+spec['type'])
#                        if param_values:
#                            templates = template_obj.search([('name','=',param_values)])
#                            if templates:
#                                template = templates[0]
#                                criteria = [('left_usages','=',spec['left']),('state','=','closed'),('refuse_renew','=',False),('type_id','in',type_ids),('id','in',this_month_used_sub_ids)]
#                                if spec['type'][3:4] == 'G':
#                                    criteria.append( ('price','>',-0.01) )
#                                    criteria.append( ('price','<',0.01) )
#                                else:
#                                    criteria.append( ('price','>',0.01) )
#                                free_to_renew_call1_ids = sub_obj.search(criteria)
##                                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'%i subscriptions to check\n' % len(free_to_renew_call1_ids))
#                                if free_to_renew_call1_ids:
#                                    renew_obj = self.pool.get('premium_subscription.renew')
#                                    subs = free_to_renew_call1_ids #sub_obj.browse(cr,uid,free_to_renew_call1_ids)
#                                    already_renewed = 0
#                                    done_renewals = 0
#                                    no_email = []
#                                    sended = []
#                                    for sub in subs:
#                                        # search if new subscription for press review already exists in the future for this contact_id
#                                        existing_sub_ids = sub_obj.search([('contact_id','=',sub.contact_id.id),('type_id','in',type_ids),('end','>',sub.end),('state','in',['current','draft'])])
#                                        if not existing_sub_ids:
#                                            renew_ids = renew_obj.search([('subscription_id','=',sub.id),('type','=',spec['type'])])
#                                            if not renew_ids: # if renew_ids, this subscription has already been send to renew
#                                                email_address = False
#                                                if sub.specific_email:
#                                                    email_address = sub.specific_email
#                                                else: # To be Fixed
#                                                    # search for email address to use
#                                                    if sub.contact_id and sub.partner_id and sub.contact_id.other_contact_ids:
#                                                        for job in sub.contact_id.other_contact_ids:
#                                                            if job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id and job.email:
#                                                                email_address = job.email
#                                                    if (not email_address) and sub.contact_id and sub.contact_id.email:
#                                                        email_address = sub.contact_id.email
#                                                    elif (not email_address) and sub.contact_id and sub.contact_id.job_email:
#                                                        email_address = sub.contact_id.job_email
#                                                    if not email_address and sub.contact_id and sub.contact_id.other_contact_ids:
#                                                        min_sequence = 999
#                                                        for job in sub.contact_id.other_contact_ids:
#                                                            if job.email and job.address_id and job.address_id.partner_id and job.address_id.partner_id.id == sub.partner_id.id:
#                                                                if job.sequence_contact < min_sequence:
#                                                                    email_address = job.email
#                                                                    min_sequence = job.sequence_contact
#                                                if email_address:
#                                                    full_texts = personalize_texts(self,sub,tags,[template.subject,template.body],'MAGG1')
#                                                    # sending of the email
#                                                    tools.email_send('abonnements@ccilvn.be', [email_address,], full_texts[0], full_texts[1], subtype=template.type)
#                                                    #tools.email_send('abonnements@ccilvn.be', ['philmer.vdm@gmail.com',], full_texts[0], full_texts[1], subtype=template.type)
#                                                    #
#                                                    sended.append(email_address)
#                                                    renew_obj.create({'name':spec['renew_name'],'subscription_id':sub.id,'date':datetime.date.today().strftime('%Y-%m-%d'),'email':email_address,'type':spec['type']})
#                                                else:
#                                                    no_email.append(sub.id)
#                                                    final_result = False
#                                                    send_todo_renew_mail(sub)
##                                                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free CCI Mag [subscriptionID %i]: no email address found\n' % sub.id)
#                                            else:
#
#                                                done_renewals += 1
#                                        else:
#                                            already_renewed += 1
##                                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Results :\nSended Emails : %s\nNo Email Subscription IDS : %s\nAlready Renewed : %i\nAlready sended Renewals : %i' % (
##                                                                                                                                             sended and (','.join(sended)) or '-/-',
##                                                                                                                                             no_email and (','.join([str(x) for x in no_email])) or '-/-',
##                                                                                                                                             already_renewed,
##                                                                                                                                             done_renewals,))
#                            else:
##                                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free CCI Mag : Wrong Template ID\n')
#                                final_result = False
#                        else:
##                             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free CCI Mag : No Template\n')
#                            final_result = False
#                    else:
##                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free CCI Mag : type unfound\n')
#                        final_result = False
#                else:
##                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'Impossible to renew Free CCI Mag : no publications extracted this month\n')
#                    final_result = False
##         self.pool.get('cci_logs.cron_line')._stop(cr,uid,cronline_id,final_result,'\n---end---')
#        return True
#
#class premium_subscription_usage(models.Model):
#    _name = "premium_subscription.usage"
#    _description = "Usage of Subscriptions for an issue of magazine"
#    
#    name = fields.Char('Name',size=60)
#    issue_id = fields.Many2one('sale.advertising.issue','Issue')
#    subscription_id = fields.Many2one('premium_subscription','Subscription')
#    date = fields.Date('Date',default=fields.Date.today())
#    active = fields.Boolean('Active', default=True)
#
#    _order = 'date desc'
#premium_subscription_usage()
#
#class premium_sub_renew(models.Model):
#    _name = "premium_subscription.renew"
#    _description = "Record of sending of renew of subscriptions"
#    
#    name = fields.Char('Name',size=60)
#    subscription_id = fields.Many2one('premium_subscription','Subscription',required=True)
#    date = fields.Date('Date' , default= fields.Date.today())
#    email = fields.Char('Email',size=200)
#    type = fields.Char('Type',size=10)
#        # RDP|MAG|PAP|REP = revuie de presse, CCI Mag, invitations papier, page pleine répertoire membre électronique
#        # G|P = renouvellement pour type Gratuit ou Payant
#        # 1|2|3 = niveau de rappel (1 = premier appel, 2 = premier rappel, 3 = second rappel)
#
#    _order = 'date desc'
#
#class res_partner_contact(models.Model):
#    _inherit = "res.partner"
#    _description = "res.partner.contact"
#    
#    subscription_ids =  fields.One2many('premium_subscription','contact_id','Subscriptions')


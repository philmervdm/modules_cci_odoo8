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
# Version 5.0.2 : Philmer 2011-06-11 Added support of fiscal_position in product_lines
from openerp import models, fields , api , _
from openerp.exceptions import Warning

from dateutil.relativedelta import relativedelta
import time
from datetime import datetime
import datetime

from openerp.addons.product._common import rounding

STATE = [
    ('none', 'Non Member'),
    ('canceled', 'Cancelled Member'),
    ('old', 'Old Member'),
    ('waiting', 'Waiting Member'),
    ('invoiced', 'Invoiced Member'),
    ('associated', 'Associated Member'),
    ('free', 'Free Member'),
    ('paid', 'Paid Member'),
]

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'res.partner'

    asker_name = fields.Char('Asker Name',size=50)
    asker_address = fields.Char('Asker Address',size=50)
    asker_zip_id = fields.Many2one('res.partner.zip','Asker Zip Code')
    sender_name = fields.Char('Sender Name',size=50)
    insurer_id = fields.Char('Insurer ID',size=50)


class cci_missions_site(models.Model):
    _name = 'cci_missions.site'
    _description = 'cci_missions.site'

    name = fields.Char('Name of the Site',size=50,required=True)
    official_name_1 = fields.Char('Official Name of the Site',size=50,required=True)
    official_name_2 = fields.Char('Official Name of the Site',size=50)
    official_name_3 = fields.Char('Official Name of the Site',size=50)
    official_name_4 = fields.Char('Official Name of the Site',size=50)
    embassy_sequence_id = fields.Many2one('ir.sequence','Sequence for Embassy Folder',required=True)


class cci_missions_embassy_folder(models.Model):
    _name = 'cci_missions.embassy_folder'
    _description = 'cci_missions.embassy_folder'
    _inherits = {'crm.lead': 'crm_case_id'}

    @api.multi
    def cci_mission_send(self):
        #There is no Stage with Status = "pending'
#         self.write({'state':'pending'})
#         cases = self.browse(cr, uid, ids)
#         self._history(cr, uid, cases, 'Send', history=True,)
        return True

    @api.multi
    def cci_mission_got_back(self):
#         self.write(cr, uid, ids, {'state':'open'})
#         cases = self.browse(cr, uid, ids)
#         self._history(cr, uid, cases, _('Got Back'), history=True)
        for id in self:
            data = {}
            obj_folder_line = self.env['cci_missions.embassy_folder_line']
            temp = obj_folder_line.search([('folder_id','=',id.id),('type','=','Translation')])
            if temp:
                translation_line = temp[0] #obj_folder_line.browse(cr, uid, [temp[0]])[0]
                if translation_line.awex_eligible:# and id.partner_id.awex_eligible == 'yes':
                    #look for an existing credit line in the current time
                    credit_line = self.env['credit.line'].search([('from_date','<=',time.strftime('%Y-%m-%d')), ('to_date', '>=', time.strftime('%Y-%m-%d'))])
                    if credit_line:
                        #if there is one available: get available amount from it
                        amount = self.env['credit.line'].get_available_amount(translation_line.customer_amount, id.partner_id.id)
                        if amount > 0:
                            data['awex_amount'] = amount
                            data['credit_line_id'] =  credit_line[0].id
                        else:
                            data['awex_eligible'] = False
                    translation_line.write(data)
        return True

    @api.multi
    def _cci_mission_done_folder(self):
        self.write({'state':'done','invoice_date': time.strftime('%Y-%m-%d %H:%M:%S')})
#         cases = self.browse(cr, uid, ids)
#         self._history(cr, uid, cases, _('Invoiced'), history=True)
        return True

    @api.model
    def _history(self, temp, keyword):
        for case in temp:
            data = {
                'name': keyword,
#                 'som': case.som.id,
#                 'canal_id': case.canal_id.id,
                'user_id': self.env.uid,
                'case_id': case.crm_case_id.id
            }
            obj = self.env['crm.case.log']
            obj.create(data)
        return True

    @api.model
    def create(self, vals):
#       Overwrite the name field to set next sequence according to the sequence in for the embassy folder related in the site_id
        if vals.get('site_id',False):
            data = self.env['cci_missions.site'].browse(vals['site_id'])
            seq = self.env['ir.sequence'].get(data.embassy_sequence_id.code)
            if seq:
                vals.update({'name': seq})
        temp = super(cci_missions_embassy_folder,self).create(vals)
#         self._history(temp, _('Created'))
        return temp

    @api.multi
    def onchange_partner_id(self,part):
        warning = False
        if not part:
            return {'value':{}}
        part_obj = self.env['res.partner']
        data_partner = part_obj.browse(part)
        if data_partner.alert_legalisations:
                warning = {
                    'title': _("Warning:"),
                    'message': data_partner.alert_explanation or _('Partner is not valid')
                        }
#         addr = part_obj.address_get([part], ['contact'])
#         data = {'partner_address_id':addr['contact']}
        if warning:
            return {'warning': warning}
        return {'value':{}}

    @api.constrains('embassy_folder_line_ids')
    def check_folder_line(self):
        #CONSTRAINT: For each embassy Folder, it can only be one embassy_folder_line of each type.
#         data_folder = self.browse(cr,uid,ids)
        list = []
        for folder in self:
            for line in folder.embassy_folder_line_ids:
                if line.type and line.type in list:
                    raise Warning(_('Error :'), _('Only One Embassy Folder line allowed for each type!'))
                list.append(line.type)
        return True

    crm_case_id = fields.Many2one('crm.lead','Lead', ondelete='cascade',required=True)
    member_price = fields.Boolean('Member Price Allowed')
    customer_reference = fields.Char('Folders Reference for the Customer',size=30)
    destination_id = fields.Many2one('cci.country','Destination Country', domain=[('valid4embassy','=',True)])
    link_ids = fields.One2many('cci_missions.dossier','embassy_folder_id','Linked Documents')
    internal_note = fields.Text('Internal Note')
    invoice_note = fields.Text('Note to Display on the Invoice',help='to display as the last embassy_folder_line of this embassy_folder.')
    embassy_folder_line_ids = fields.One2many('cci_missions.embassy_folder_line','folder_id','Details')
    site_id = fields.Many2one('cci_missions.site','Site', required=True)
    invoice_date = fields.Datetime('Invoice Date', readonly=True) 
    invoice_id = fields.Many2one("account.invoice","Invoice")
    embassy_date = fields.Datetime(related='crm_case_id.create_date', string="Date", store=True)

    _defaults = {
        'section_id': lambda obj, cr, uid, context: obj.pool.get('crm.case.section').search(cr, uid, [('name','=','Embassy Folder')])[0],
        'name': '/',
        'state' : 'draft',
        "create_date": lambda *a: time.strftime("%Y-%m-%d %H:%M:%S")
    }
    _order = "embassy_date desc"

class cci_missions_embassy_folder_line(models.Model):
    _name = 'cci_missions.embassy_folder_line'
    _description = 'cci_missions.embassy_folder_line '

    @api.model
    def create(self, vals):
        t_name = ''
        if vals.get('folder_id'):
            site_id = self.env['cci_missions.embassy_folder'].browse(vals['folder_id']).site_id
            t_name = site_id.name
        prod_name= vals['type'] + str(' Product ') + t_name
        self.env.cr.execute('select id from product_template where name='"'%s'"''%str(prod_name))
        prod = self.env.cr.fetchone()

        if prod:
            product_id = prod[0]
            prod_info = self.env['product.product'].browse(product_id)
            account =  prod_info.product_tmpl_id.property_account_income.id
            if not account:
                account = prod_info.categ_id.property_account_income_categ.id
            vals['account_id'] = account
            vals['product_id'] = product_id
        return super(cci_missions_embassy_folder_line,self).create(vals)

    @api.multi
    def write(self,vals):
        folder_line_id = self #self.pool.get('cci_missions.embassy_folder_line').browse(cr, uid, ids)
        site_id = folder_line_id and folder_line_id[0].folder_id and folder_line_id[0].folder_id.site_id or False
        if vals.has_key('type'):
            prod_name = vals['type'] + str(' Product ') + (site_id and site_id.name or '')
            self.env.cr.execute('select id from product_template where name='"'%s'"''%str(prod_name))
            prod = self.env.cr.fetchone()
            if prod:
                product_id = prod[0]
                prod_info = self.env['product.product'].browse(product_id)
                account =  prod_info.product_tmpl_id.property_account_income.id
                if not account:
                    account = prod_info.categ_id.property_account_income_categ.id
                vals['account_id'] = account
                vals['product_id'] = product_id
        return super(cci_missions_embassy_folder_line,self).write(vals)

    @api.multi
    def onchange_line_type(self,type,site_id=False,partner_id=False):
        #print type
        #print site_id
        #print partner_id
        data={}
        data['courier_cost'] = data['customer_amount'] = data['account_id'] = data['name']=False
        if not type:
            return {'value' : data }

        data['name'] = type
        prod = False
        if site_id:
            site_id = self.env['cci_missions.site'].browse(site_id)
            prod_name = str(type) + str(' Product ') + site_id.name
            self.env.cr.execute('select id from product_template where name='"'%s'"''%str(prod_name))
            prod = self.env.cr.fetchone()
        if not prod:
            return {'value' : data }

        product_id = prod[0]
        prod_info = self.env['product.product'].browse(product_id)
        data['courier_cost'] = prod_info.standard_price
        data['customer_amount'] = prod_info.list_price
        data['tax_rate'] = prod_info.taxes_id and prod_info.taxes_id[0].id or False
        account =  prod_info.product_tmpl_id.property_account_income.id
        if not account:
            account = prod_info.categ_id.property_account_income_categ.id
        data['account_id'] = account
        if partner_id:
            # take fiscal_position into account
            partner = self.env['res.partner'].browse(partner_id)
            fiscal_position_id = partner.property_account_position and partner.property_account_position.id or False
            fiscal_position = fiscal_position_id and self.env['account.fiscal.position'].browse(fiscal_position_id) or False
            account_id = self.env['account.fiscal.position'].map_account(data['account_id'])
            if account_id:
                data['account_id'] = account_id
            if data['tax_rate']:
                taxes = [self.env['account.tax'].browse(data['tax_rate'])]
                tax_id = self.env['account.fiscal.position'].map_tax(taxes)
                if tax_id:
                    data['tax_rate'] = tax_id[0]
            # end fiscal position
        return {'value' : data }

    name = fields.Char('Description',size=50,required=True)
    folder_id = fields.Many2one('cci_missions.embassy_folder','Related Embassy Folder',required=True)
    courier_cost = fields.Float('Couriers Costs')
    customer_amount = fields.Float('Invoiced Amount')
    tax_rate = fields.Many2one('account.tax','Tax Rate')
    type = fields.Selection([('CBA','CBA'),('Ministry','Ministry'),('Embassy Consulate','Embassy Consulate'),('Translation','Translation'),('Administrative','Administrative'),('Travel Costs','Travel Costs'),('Others','Others')],'Type',required=True)
    account_id = fields.Many2one('account.account', 'Account')
    awex_eligible = fields.Boolean('AWEX Eligible')
    awex_amount = fields.Float('AWEX Amount', readonly=True)
    credit_line_id = fields.Many2one('credit.line', 'Credit Line', readonly=True)
    product_id = fields.Many2one('product.product','Product',readonyl=True)

class cci_missions_dossier_type(models.Model):
    _name = 'cci_missions.dossier_type'
    _description = 'cci_missions.dossier_type'

    code =  fields.Char('Code',size=3,required=True)
    name =  fields.Char('Description',size=50,required=True)
    original_product_id =  fields.Many2one('product.product','Reference for Original Copies',required=True,help='for the association with a pricelist')
    copy_product_id =  fields.Many2one('product.product','Reference for Copies',required=True,help='for the association with a pricelist')
    site_id =  fields.Many2one('cci_missions.site','Site',required=True)
    sequence_id =  fields.Many2one('ir.sequence','Sequence',required=True,help='for association with a sequence')
    section =  fields.Selection([('certificate','Certificate'),('legalization','Legalization'),('ATA','ATA Carnet')],'Type',required=True)
    warranty_product_1 = fields.Many2one('product.product', 'Warranty product for ATA carnet if Own Risk')
    warranty_product_2 = fields.Many2one('product.product', 'Warranty product for ATA carnet if not own Risk')
    id_letter =  fields.Char('ID Letter', size=1, help='for identify the type of certificate by the federation' )
    digital =  fields.Boolean('Digital certificate')

class cci_missions_dossier(models.Model):
    _name = 'cci_missions.dossier'
    _description = 'cci_missions.dossier'

    @api.model
    def create(self,vals):
        #overwrite the create: if the text_on_invoice field is empty then fill it with name + destination_id.name + (quantity_original)
        if not vals.has_key('text_on_invoice') or not vals['text_on_invoice']:
            invoice_text = vals['name']
            if vals.get('destination_id'):
                destination_data = self.env['cci.country'].browse(vals['destination_id'])
                invoice_text = vals['name'] + ' ' + destination_data.name + ' (' + str(vals['quantity_original'])  + ')'
            vals.update({'text_on_invoice': invoice_text})
        return super(cci_missions_dossier,self).create(vals)

    @api.multi
    def get_partner_details(self,order_partner_id):
        result={}
        asker_name=False
        sender_name=False
        if order_partner_id:
            partner_info = self.env['res.partner'].browse(order_partner_id)
            if not partner_info.asker_name:
                asker_name=partner_info.name
            else:
                asker_name=partner_info.asker_name
            if not partner_info.sender_name:
                sender_name=partner_info.name
            else:
                sender_name=partner_info.sender_name
        result = {'value': {
            'asker_name': asker_name,
            'sender_name': sender_name}
        }
        return result

    @api.depends('product_ids')
    def _amount_subtotal(self):
        for data in self:
            sum=0.00
            for product in data.product_ids:
                sum += product.price_subtotal
            data.sub_total = sum

    id = fields.Integer('ID', readonly=True)
    name = fields.Char('Reference',size=20,required=True, default='/')
    type_id = fields.Many2one('cci_missions.dossier_type','Dossier Type',required=True)
    date = fields.Date('Creation Date',required=True, default=fields.Date.today())
    order_partner_id = fields.Many2one('res.partner','Billed Customer',required=True)
    asker_name = fields.Char('Asker Name',size=50)
    sender_name = fields.Char('Sender Name',size=50)
    to_bill = fields.Boolean('To Be Billed', default=True)
    state = fields.Selection([('draft','Confirmed'),('invoiced','Invoiced'),('cancel_customer','Canceled by Customer'),('cancel_cci','Canceled by the CCI')],default='draft',string='State',)
    goods = fields.Char('Goods Description',size=100)
    goods_value = fields.Float('Value of the Sold Goods')#Monetary; must be greater than zero
    destination_id = fields.Many2one('cci.country','Destination Country', domain=[('valid4certificate','=',True)])
    embassy_folder_id = fields.Many2one('cci_missions.embassy_folder','Related Embassy Folder')
    quantity_copies = fields.Integer('Number of Copies')
    quantity_original = fields.Integer('Quantity of Originals',default=1,required=True)
    sub_total = fields.Float(compute='_amount_subtotal', string='Sub Total for Extra Products', store=True)
    text_on_invoice = fields.Text('Text to Display on the Invoice')
    product_ids =  fields.One2many('product.lines', 'dossier_product_line_id', 'Products')
    invoice_id = fields.Many2one("account.invoice","Invoice")
    invoiced_amount = fields.Float('Total')
    
    _order = "date desc"


class cci_missions_custom_code(models.Model):
    _name= 'cci_missions.custom_code'
    _description = 'cci_missions.custom_code'
    
    name = fields.Char('Name',size=8,required=True)
    meaning = fields.Text('Meaning',required=True)
    official = fields.Boolean('Official Code')


class cci_missions_certificate(models.Model):
    _name = 'cci_missions.certificate'
    _description = 'cci_missions.certificate'
    _inherits = {'cci_missions.dossier': 'dossier_id' }

    @api.depends('state','type_id','order_partner_id','date','goods_value','quantity_original','quantity_copies')
    def _amount_total(self):
        res ={}
        for data in self:
            if data.state =='draft':
                ctx = self.env.context.copy()
                data_partner = data.order_partner_id #self.env['res.partner'].browse(data.order_partner_id.id)
                ctx.update({'partner':data_partner.id})
                ctx.update({'force_member':False})
                ctx.update({'force_non_member':False})
                ctx.update({'date':data.date})
                ctx.update({'value_goods':data.goods_value})
                ctx.update({'pricelist':data_partner.property_product_pricelist.id})
                price_org = data.type_id.original_product_id.with_context(ctx)._product_price(False, False)
                price_copy = data.type_id.copy_product_id.with_context(ctx)._product_price(False, False)
                cost_org = price_org.get(data.type_id.original_product_id.id,False)
                cost_copy = price_copy.get(data.type_id.copy_product_id.id,False)
                qty_org = data.quantity_original
                qty_copy = data.quantity_copies
                subtotal =  data.sub_total
                if qty_org < 0 or qty_copy < 0:
                    raise Warning(_('Input Error!'),_('No. of Copies and Quantity of Originals should be positive.'))
                total = ((cost_org * qty_org ) + (cost_copy * qty_copy) + subtotal)
                self.total = total
            else :
                self.total = data.invoiced_amount

    @api.multi
    def cci_dossier_cancel_cci(self):
        data = self #self.browse(cr,uid,ids[0])
        if data.invoice_id:
            if data.invoice_id.state == 'paid':
                new_ids = self.env['account.invoice'].refund([data.invoice_id.id])
                self.write({'invoice_id' : new_ids[0]})
            else:
                data.invoice_id.signal_workflow('invoice_cancel')
#                 wf_service = netsvc.LocalService('workflow')
#                 wf_service.trg_validate(uid, 'account.invoice', data.invoice_id.id, 'invoice_cancel', cr)
        self.write({'state':'cancel_cci',})
        return True

    @api.multi
    def get_certification_details(self,order_partner_id):
        result={}
        asker_name=False
        sender_name=False
        asker_address=False
        zip=False
        warning = False

        if order_partner_id:
            partner_info = self.env['res.partner'].browse(order_partner_id)
            if partner_info.alert_legalisations:
                warning = {
                    'title': _("Warning:"),
                    'message': partner_info.alert_explanation or _('Partner is not valid')
                        }
            if not partner_info.asker_name:
                asker_name=partner_info.name
            else:
                asker_name=partner_info.asker_name
            if not partner_info.sender_name:
                sender_name=partner_info.name
            else:
                sender_name=partner_info.sender_name
            if not partner_info.asker_address:
                if partner_info.child_ids!=[]:
                    for add in partner_info.child_ids:
                        if add.type=='default':
                            asker_address=add.street
                            break
            else:
                asker_address=partner_info.asker_address
            if not partner_info.asker_zip_id.id:
                if partner_info.child_ids!=[]:
                    for add in partner_info.child_ids:
                        if add.type=='default':
                            zip=add.zip_id.id
                            break
            else:
                zip=partner_info.asker_zip_id.id

        result = {'value': {
            'asker_name': asker_name,
            'asker_address': asker_address,
            'asker_zip_id': zip,
            'sender_name': sender_name}
        }
        if warning:
            result['warning'] =  warning
        return result

    @api.model
    def create(self, vals):
#       Overwrite the name fields to set next sequence according to the sequence in the certification type (type_id)
        if vals.get('type_id'):
            data = self.env['cci_missions.dossier_type'].browse(vals['type_id'])
            seq = self.env['ir.sequence'].get(data.sequence_id.code)
            if seq:
                vals.update({'name': seq})
        return super(cci_missions_certificate,self).create(vals)

    @api.constrains('digital_number')
    def check_digital_no(self):
        for data in self:
            if data.digital_number and not data.type_id.digital:
                raise Warning(_('Error!'),_('Only 11 Digits allowed, for digital certificates only and with associated product !'))
            if data.type_id.digital and not data.digital_number:
                raise Warning(_('Error!'),_('Only 11 Digits allowed, for digital certificates only and with associated product !'))
            if data.digital_number and not data.digital_number.isdigit():
                raise Warning(_('Error!'),_('Only 11 Digits allowed, for digital certificates only and with associated product !'))
            if data.digital_number and len( data.digital_number ) != 11:
                raise Warning(_('Error!'),_('Only 11 Digits allowed, for digital certificates only and with associated product !'))
            if data.digital_number and len( data.product_ids ) == 0:
                raise Warning(_('Error!'),_('Only 11 Digits allowed, for digital certificates only and with associated product !'))
        return True

    dossier_id = fields.Many2one('cci_missions.dossier','Dossier', ondelete='cascade',required=True)
    total = fields.Float(compute='_amount_total', string='Total', store=True) # sum of the price for copies, originals and extra_products
    asker_address = fields.Char('Asker Address',size=50)#by default, res.partner->asker_adress or, res_partner.address[default]->street
    asker_zip_id = fields.Many2one('res.partner.zip','Asker Zip Code')#by default, res.partner->asker_zip_id or, res_partner.address[default]->zip_id
    special_reason = fields.Selection([('none','None'),('Commercial Reason','Commercial Reason'),('Substitution','Substitution')],default='none',string='For special cases')
    legalization_ids = fields.One2many('cci_missions.legalization','certificate_id','Related Legalizations')
    customs_ids = fields.Many2many('cci_missions.custom_code','certificate_custome_code_rel','certificate_id','custom_id','Custom Codes')
    sending_spf = fields.Date('SPF Sending Date',help='Date of the sending of this record to the external database')
    origin_ids = fields.Many2many('cci.country','certificate_country_rel','certificate_id','country_id','Origin Countries',domain=[('valid4certificate','=',True)])
    date_certificate = fields.Date(related='dossier_id.date', string="Creation Date", store=True)
    digital_number = fields.Char('Digital Number', size=11, help='Please Enter only digits for Digital Number')

    _order = "date_certificate desc"

class cci_missions_legalization(models.Model):
    _name = 'cci_missions.legalization'
    _description = 'cci_missions.legalization'
    _inherits = {'cci_missions.dossier': 'dossier_id'}

    @api.depends('state','order_partner_id','date','goods_value','quantity_original','quantity_copies')
    def _amount_total(self):
        for data in self:
            if data.state =='draft':
                data_partner = self.env['res.partner'].browse(data.order_partner_id.id)

                force_member=force_non_member=False
                
                if data.member_price == 1:
                    force_member=True
                else:
                    force_non_member=True
                
                ctx = self.env.context.copy()
                ctx.update({'partner':data_partner.id})
                ctx.update({'force_member':force_member})
                ctx.update({'force_non_member':force_non_member})
                ctx.update({'date':data.date})
                ctx.update({'value_goods':data.goods_value})
                ctx.update({'pricelist':data_partner.property_product_pricelist.id})
                
                price_org = data.type_id.original_product_id.with_context(ctx)._product_price(False, False)
                price_copy = data.type_id.copy_product_id.with_context(ctx)._product_price(False, False)
                cost_org = price_org.get(data.type_id.original_product_id.id,0.0)
                cost_copy=price_copy.get(data.type_id.copy_product_id.id,0.0)
                qty_org = data.quantity_original
                qty_copy = data.quantity_copies
                subtotal =  data.sub_total

                if qty_org < 0 or qty_copy < 0:
                    raise Warning(_('Input Error!'),_('No. of Copies and Quantity of Originals should be positive.'))
                total = ((cost_org * qty_org ) + (cost_copy * qty_copy) + subtotal)
                data.total = total
            else :
                data.total = data.invoiced_amount

    @api.multi
    def cci_dossier_cancel_cci(self):
        data = self #self.browse(cr,uid,ids[0])
        if data.invoice_id: 
            if data.invoice_id.state == 'paid':
                new_ids = self.env['account.invoice'].refund([data.invoice_id.id])
                self.write({'invoice_id' : new_ids[0].id})
            else:
                data.invoice_id.signal_workflow('invoice_cancel')
#                 wf_service = netsvc.LocalService('workflow')
#                 wf_service.trg_validate(uid, 'account.invoice', data.invoice_id.id, 'invoice_cancel', cr)
                
        self.write({'state':'cancel_cci',})
        return True

    @api.multi
    def get_legalization_details(self,order_partner_id):
        result={}
        asker_name=False
        sender_name=False
        member_state=False
        warning = False
        
        if order_partner_id:
            partner_info = self.env['res.partner'].browse(order_partner_id)
            if partner_info.alert_legalisations:
                warning = {
                    'title': _("Warning:"),
                    'message': partner_info.alert_explanation or _('Partner is not valid')
                        }
            
            if partner_info.membership_state in ('none','canceled'): #the boolean "Apply the member price" should be set to TRUE or FALSE when the partner is changed in regard of the membership state of him.
                member_state = False
            else:
                member_state = True
                
            if not partner_info.asker_name:
                asker_name=partner_info.name
            else:
                asker_name=partner_info.asker_name
            if not partner_info.sender_name:
                sender_name=partner_info.name
            else:
                sender_name=partner_info.sender_name
        
        result = {'value': {
            'asker_name': asker_name,
            'sender_name': sender_name,
            'member_price':member_state
            }
        }
        if warning:
            result['warning'] = warning
        return result

    @api.model
    def create(self, vals):
#       Overwrite the name fields to set next sequence according to the sequence in the legalization type (type_id)
        if vals.get('type_id'):
            data = self.env['cci_missions.dossier_type'].browse(vals['type_id'])
            seq = self.env['ir.sequence'].get(data.sequence_id.code)
            if seq:
                vals.update({'name': seq})
        return super(cci_missions_legalization,self).create(vals)

    @api.depends('dossier_id','dossier_id.order_partner_id')
    def _get_member_state(self):
        for p_id in self:
            partner_member_state = p_id.dossier_id.order_partner_id.membership_state

    @api.constrains('quantity_original')
    def check_orig(self):
        for data in self:
            if data.quantity_original <= 0:
                raise Warning(_('Error :'), _('The number of originals must be stricly superior to 0 !'))
        return True

    dossier_id = fields.Many2one('cci_missions.dossier','Dossier', ondelete='cascade',required=True)
    total = fields.Float(compute='_amount_total', string='Total', store=True)# sum of the price for copies, originals and extra_products
    certificate_id = fields.Many2one('cci_missions.certificate','Related Certificate')
    partner_member_state = fields.Selection(compute='_get_member_state',selection=STATE,string='Member State of the Partner',readonly=True,type="selection")
    member_price = fields.Boolean('Apply the Member Price')
    date_legalization = fields.Date(related='dossier_id.date', string="Creation Date", store=True)

    _order = "date_legalization desc"


class cci_missions_courier_log(models.Model):
    _name = 'cci_missions.courier_log'
    _description = 'cci_missions.courier_log'

    embassy_folder_id = fields.Many2one('cci_missions.embassy_folder','Related Embassy Folder',required=True)
    cba =  fields.Boolean('CBA')
    ministry =  fields.Boolean('Ministry')
    translation = fields.Boolean('Translation')
    embassy_name = fields.Char('Embassy Name',size=30)
    consulate_name = fields.Char('Consulate Name',size=30)
    others = fields.Char('Others',size=200)
    copy_cba = fields.Boolean('Photocopy Before CBA')
    copy_ministry = fields.Boolean('Photocopy Before Ministry')
    copy_embassy_consulate = fields.Boolean('Photocopy Before Embassy or Consulate')
    documents = fields.Integer('Number of Documents to Legalize')
    documents_certificate = fields.Text('List of Certificates')
    documents_invoice = fields.Text('List of Invoices')
    documents_others = fields.Text('Others')
    message = fields.Text('Message to the Courier')
    return_address = fields.Selection([('A la CCI','A la CCI'),('Au client','Au client')],string='Address of Return',required=True)
    address_name_1 = fields.Char('Company Name',size=80)
    address_name_2 = fields.Char('Contact Name',size=80)
    address_street = fields.Char('Street',size=80)
    address_city = fields.Char('City',size=80)
    qtty_to_print = fields.Integer('Number of Sheets')
    partner_address_id = fields.Many2one('res.partner','Courier')

#~ class cci_missions_area(osv.osv):
    #~ _name = 'cci_missions.area'
    #~ _description = 'cci_missions.area'
    #~ _columns = {
        #~ 'name = fields.Char('Description',size=50,required=True,translate=True),
        #~ 'country_ids': fields.Many2many('res.country','area_country_rel','area','country',"Countries"),
    #~ }

#~ cci_missions_area()

class cci_missions_ata_usage(models.Model):
    _name = 'cci_missions.ata_usage'
    _description = 'cci_missions.ata_usage'
    
    name = fields.Char('Usage',size=80,required=True)


class cci_missions_ata_carnet(models.Model):
    _name = 'cci_missions.ata_carnet'
    _description = 'cci_missions.ata_carnet'

    @api.model
    def create(self, vals):
        context = {}
        data_partner = self.env['res.partner'].browse(vals['partner_id'])
        context.update({'pricelist':data_partner.property_product_pricelist.id})

        if 'creation_date' in vals:
            context.update({'date':vals['creation_date']})
            context.update({'emission_date':vals['creation_date']})
        if 'partner_id' in vals:
            context.update({'partner_id':vals['partner_id']})
        if 'goods_value' in vals:
            context.update({'value_goods':vals['goods_value']})
        if 'double_signature' in vals:
            context.update({'double_signature':vals['double_signature']})
        force_member = force_non_member = False
        if 'member_price' in vals and vals['member_price']==1:
            force_member=True
        else:
            force_non_member=True
        context.update({'force_member':force_member})
        context.update({'force_non_member':force_non_member})

        data = self.env['cci_missions.dossier_type'].browse(vals['type_id'])
        if 'own_risk' in vals and vals['own_risk']:
            warranty_product = data.warranty_product_1.id
        else:
            warranty_product = data.warranty_product_2.id

#        warranty= self.pool.get('product.product').price_get(cr,uid,[warranty_product],'list_price', context)[warranty_product]
        vals.update({'warranty_product_id' : warranty_product})  #'warranty': warranty

        seq = self.env['ir.sequence'].get(data.sequence_id.code)
        if seq:
            vals.update({'name': seq})
        return super(cci_missions_ata_carnet,self).create(vals)

    @api.multi
    def write(self,vals):
#         data_carnet = self #self.browse(cr,uid,ids[0])
        for data_carnet in self:
            context = {}
            if 'creation_date' in vals:
                context.update({'date':vals['creation_date']})
                context.update({'emission_date':vals['creation_date']})
            else:
                context.update({'date':data_carnet.creation_date})
                context.update({'emission_date':data_carnet.creation_date})
    
            if 'partner_id' in vals:
                context.update({'partner_id':vals['partner_id']})
                data_partner = self.env['res.partner'].browse(vals['partner_id'])
            else:
                context.update({'partner_id':data_carnet.partner_id.id})
                data_partner = self.env['res.partner'].browse(data_carnet.partner_id.id)
    
            if 'goods_value' in vals:
                context.update({'value_goods':vals['goods_value']})
            else:
                context.update({'value_goods':data_carnet.goods_value})
                
            if 'double_signature' in vals:
                context.update({'double_signature':vals['double_signature']})
            else:
                context.update({'double_signature':data_carnet.double_signature})
            
            force_member=force_non_member=False
    
            context.update({'pricelist':data_partner.property_product_pricelist.id})
            
            if 'member_price' in vals:
                if vals['member_price']==1:
                    force_member=True
                else:
                    force_non_member=True
            else:
                if data_carnet.member_price==1:
                    force_member=True
                else:
                    force_non_member=True
                    
            context.update({'force_member':force_member})
            context.update({'force_non_member':force_non_member})
    
            if 'own_risk' in vals:
                if vals['own_risk']:
                    warranty_product = data_carnet.type_id.warranty_product_1.id
                else:
                    warranty_product = data_carnet.type_id.warranty_product_2.id
            else:
                if data_carnet.own_risk:
                    warranty_product = data_carnet.type_id.warranty_product_1.id
                else:
                    warranty_product = data_carnet.type_id.warranty_product_2.id
    #        warranty= self.pool.get('product.product').price_get(cr,uid,[warranty_product],'list_price', context)[warranty_product]
            vals.update({'warranty_product_id' : warranty_product}) #, 'warranty': warranty
            super(cci_missions_ata_carnet,self).write(vals)
        return True

    @api.multi
    def button_uncertain(self):
        self.write({'state':'pending'})
        return True

    @api.multi
    def button_correct(self):
        self.write({'state':'correct','ok_state_date':time.strftime('%Y-%m-%d')})
        return True

    @api.multi
    def button_dispute(self):
        self.write({'state':'dispute'})
        return True

    @api.multi
    def button_closed(self):
        self.write({'state':'closed'})
        return True

    @api.multi
    def cci_ata_created(self):
        self.write({'state':'created','return_date':time.strftime('%Y-%m-%d')})
        return True

    @api.multi
    def _get_insurer_id(self):
        res={}
#         partner_ids = self.browse(cr,uid,ids)
        for p_id in self:
            self.partner_insurer_id = p_id.partner_id.insurer_id

    @api.multi
    def onchange_type_carnet(self,type_id,own_risk):
        data={'warranty_product_id' : False,'warranty':False}
        if not type_id:
            return {'value':data}
        data_carnet_type = self.env['cci_missions.dossier_type'].browse(type_id)
        if own_risk:
            warranty_prod = data_carnet_type.warranty_product_1.id
        else:
            warranty_prod = data_carnet_type.warranty_product_2.id
        data['warranty_product_id'] = warranty_prod
        dict1 = self.onchange_warranty_product_id(warranty_prod)
        data.update(dict1['value'])
        return {'value':data}

    @api.multi
    def onchange_good_value(self,creation_date, partner_id, goods_value, double_signature, member_price, own_risk, type_id):
        res = {'warranty': False}
        
        if not type_id:
            return {'value':res}
        ctx = self.env.context.copy()
        if creation_date:
            ctx.update({'date':creation_date})
            ctx.update({'emission_date':creation_date})
        if partner_id:
            ctx.update({'partner_id':partner_id})
        if goods_value:
            ctx.update({'value_goods':goods_value})
        if double_signature:
            ctx.update({'double_signature':double_signature})
        force_member = force_non_member = False
        if member_price == 1:
            force_member = True
        else:
            force_non_member = True
        ctx.update({'force_member': force_member})
        ctx.update({'force_non_member': force_non_member})

        data = self.env['cci_missions.dossier_type'].browse(type_id)
        if own_risk:
            warranty_product = data.warranty_product_1
        else:
            warranty_product = data.warranty_product_2
        res['warranty'] = warranty_product.with_context(ctx).price_get('list_price')[warranty_product.id]
        return {'value': res}

    @api.multi
    def onchange_own_risk(self,type_id,own_risk):
        data={'warranty_product_id' : False,'warranty':False}
        if not type_id:
            return {'value': data}
        warranty_prod = False
        data_carnet_type = self.env['cci_missions.dossier_type'].browse(type_id)
        if own_risk:
            warranty_prod = data_carnet_type.warranty_product_1.id
        else:
            warranty_prod = data_carnet_type.warranty_product_2.id
        data['warranty_product_id'] =warranty_prod
        dict1 = self.onchange_warranty_product_id(warranty_prod)
        data.update(dict1['value'])
        return {'value':data}

    @api.multi
    def _get_member_state(self):
        res={}
#         partner_ids = self.browse(cr,uid,ids)
        for p_id in self:
            self.partner_member_state = p_id.partner_id.membership_state
        return res

    @api.constrains('own_risk','insurer_agreement','partner_insurer_id')
    def check_ata_carnet(self):
        for data in self:
            if (data.own_risk) or (data.insurer_agreement > 0 and data.partner_id.insurer_id > 0):
                return True
        raise Warning(_('Error :'), _('Please Select (Own Risk) OR ("Insurer Agreement" and "Parnters Insure id" should be greater than Zero) !'))

    @api.model
    def _default_validity_date(self):
        creation_date = datetime.datetime.today()
        year = datetime.date(creation_date.year + 1,creation_date.month,creation_date.day)
        validity_date = year - relativedelta(days=1)
        return validity_date.strftime('%Y-%m-%d')

    @api.depends('product_ids')
    def _tot_products(self):
        for p_id in self:
            sum=0.00
            for line_id in p_id.product_ids:
                sum += line_id.price_subtotal
            self.sub_total = sum

    @api.multi
    def onchange_partner_id(self,partner_id):
        #the boolean "Apply the member price" should be set to TRUE or FALSE when the partner is changed in regard of the membership state of him.
        member_state = False
        warning = False
        res = {}
        res['value'] = {}
        
        if partner_id:
            partner_info = self.env['res.partner'].browse(partner_id)
            if partner_info.alert_legalisations:
                warning = {
                    'title': _("Warning:"),
                    'message': partner_info.alert_explanation or _('Partner is not valid')
                        }
            if partner_info.membership_state in ('none','canceled'):
                member_state = False
            else:
                member_state = True
            res['value']['partner_member_state'] = partner_info.membership_state
            res['value']['partner_insurer_id'] = partner_info.insurer_id
            res['value']['member_price'] = member_state
        if warning:
            res['warning'] = warning
        return res
    
    @api.multi
    def onchange_warranty_product_id(self,prod_id):
        warranty_price= False
        if prod_id:
            prod_info = self.env['product.product'].browse(prod_id)
            warranty_price = prod_info.list_price
        return {'value':{'warranty' : warranty_price}}

    id = fields.Integer('ID')
    type_id = fields.Many2one('cci_missions.dossier_type','Related Type of Carnet',required=True)
    creation_date = fields.Date('Emission Date',default= fields.Date.today(),required=True)
    validity_date = fields.Date('Validity Date',default=_default_validity_date,required=True)
    partner_id = fields.Many2one('res.partner','Partner',required=True)
    holder_name = fields.Char('Holder Name',size=50)
    holder_address = fields.Char('Holder Address',size=50)
    holder_city = fields.Char('Holder City',size=50)
    representer_name = fields.Char('Representer Name',size=50)
    representer_address = fields.Char('Representer Address',size=50)
    representer_city = fields.Char('Representer City',size=50)
    usage_id = fields.Many2one('cci_missions.ata_usage','Usage',required=True)
    goods = fields.Char('Goods',size=80)
    area_id = fields.Many2one('cci.country','Area',required=True,domain=[('valid4ata','=',True)])
    insurer_agreement = fields.Char('Insurer Agreement',size=50)
    own_risk = fields.Boolean('Own Risks')
    goods_value = fields.Float('Goods Value',required=True)
    double_signature = fields.Boolean('Double Signature')
    initial_pages = fields.Integer('Initial Number of Pages',required=True)
    additional_pages = fields.Integer('Additional Number of Pages')
    warranty =fields.Float('Warranty')
    warranty_product_id = fields.Many2one('product.product','Related Warranty Product',required=True)
    return_date = fields.Date('Date of Return')
    state =fields.Selection([('draft','Draft'),('created','Created'),('pending','Pending'),('dispute','Dispute'),('correct','Correct'),('closed','Closed')],'State',default='draft',required=True)
    ok_state_date = fields.Date('Date of Closure')
    federation_sending_date = fields.Date('Date of Sending to the Federation')
    name = fields.Char('Name',size=50,default='/',required=True)
    partner_insurer_id = fields.Char(compute='_get_insurer_id',string='Insurer ID of the Partner')
    partner_member_state = fields.Selection(compute='_get_member_state',selection=STATE,string='Member State of the Partner',type="selection")
    member_price = fields.Boolean('Apply the Member Price')
    product_ids = fields.One2many('product.lines', 'product_line_id', 'Products')
    letter_ids =fields.One2many('cci_missions.letters_log','ata_carnet_id','Letters')
    sub_total = fields.Float(compute='_tot_products',string='Subtotal of Extra Products',type="float", store=True)
    invoice_id = fields.Many2one("account.invoice","Invoice")

    _order = "creation_date desc"

class cci_missions_letters_log(models.Model):
    _name = 'cci_missions.letters_log'
    _description = 'cci_missions.letters_log'
    _rec_name = 'date'

    ata_carnet_id = fields.Many2one('cci_missions.ata_carnet','Related ATA Carnet',required=True)
    letter_type = fields.Selection([('Rappel avant echeance','Rappel avant echeance'),('Rappel apres echeance','Rappel apres echeance'),('Suite lettre A','Suite lettre A'),('Suite lettre C','Suite lettre C'),('Suite lettre C1','Suite lettre C1'),('Suite lettre I','Suite lettre I'),('Demande de remboursement','Demande de remboursement'),('Rappel a remboursement','Rappel a remboursement'),('Mise en demeure','Mise en demeure')],string='Type of Letter',required=True)
    date = fields.Date('Date of Sending',default= fields.Date.today() ,required=True)
    
class product_lines(models.Model):
    _name = "product.lines"
    _description = "Product Lines"

    @api.model
    def create(self, vals):
        if vals.get('product_id',False):
            accnt_dict = {}
            data_product = self.env['product.product'].browse(vals['product_id'])
            a =  data_product.product_tmpl_id.property_account_income.id
            if not a:
                a = data_product.categ_id.property_account_income_categ.id
                
            accnt_dict['account_id']=a
            vals.update(accnt_dict)
            # support of fiscal_position
            if vals.has_key('dossier_product_line_id'):
                # product associated with a certificate or a legalization
                dossier = self.env['cci_missions.dossier'].browse(vals['dossier_product_line_id'])
                partner = dossier.order_partner_id #self.env['res.partner'].browse(dossier.order_partner_id.id)
            else:
                # product associated with a carnet ATA
                #print 'Vals ATA Carnet : ' + str(vals)
                carnet_ata = self.env['cci_missions.ata_carnet'].browse(vals['product_line_id'])
                partner = carnet_ata.partner_id #self.env['res.partner'].browse(carnet_ata.partner_id.id)
                
            fiscal_position_id = partner.property_account_position and partner.property_account_position.id or False
            fiscal_position = fiscal_position_id and self.env['account.fiscal.position'].browse(fiscal_position_id) or False
            account_id = self.env['account.fiscal.position'].map_account(vals['account_id'])
            if account_id:
                vals['account_id'] = account_id
            if vals.get('taxes_id',[]):
                #vals['taxes_id'] has the format [(6,0,[id,id])]
                #print 'Before : ' + str(vals['taxes_id'])
                taxes = self.env['account.tax'].browse(vals['taxes_id'][0][2])
                #print 'Taxes : ' + str(taxes)
                tax_id = self.env['account.fiscal.position'].map_tax(taxes).ids
                #print 'New taxes : ' + str(tax_id)
                if tax_id:
                    vals['taxes_id'] = [(6,0,tax_id)]
            # end of support of fiscal_position
        return super(product_lines,self).create(vals)

    @api.multi
    def write(self,vals):
        data_product_line = self #self.pool.get('product.lines').browse(cr,uid,ids[0])
        if vals.has_key('product_id') and (not data_product_line.product_id.id == vals['product_id']):
            accnt_dict = {}
            data_product = self.env['product.product'].browse(vals['product_id'])
            a =  data_product.product_tmpl_id.property_account_income.id
            if not a:
                a = data_product.categ_id.property_account_income_categ.id
            accnt_dict['account_id']=a
            vals.update(accnt_dict)
        return super(product_lines,self).write(vals)

    @api.multi
    def _product_subtotal(self):
        res = {}
        for line in self:
            line.price_subtotal = line.price_unit * line.quantity
        return res

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        sale_taxes = []
        if self.product_id:
            data_product = self.product_id #self.env['product.product'].browse(product_id)
            self.uos_id = data_product.uom_id.id
            price = data_product.price_get()
            self.price_unit = price[self.product_id.id]
            self.name = data_product.name
            if data_product.taxes_id:
                x = map(lambda x:sale_taxes.append(x.id),data_product.taxes_id)
            self.texes_id = sale_taxes

    name = fields.Char('Description', size=256, required=True)
    product_line_id = fields.Many2one('cci_missions.ata_carnet', 'Product Ref',index=True)
    dossier_product_line_id = fields.Many2one('cci_missions.dossier', 'Product Ref',index=True)
    uos_id = fields.Many2one('product.uom', 'Unit', ondelete='set null')
    product_id = fields.Many2one('product.product', 'Product', ondelete='set null',required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=(16,2))
    price_subtotal = fields.Float(compute='_product_subtotal',string='Subtotal')
    quantity = fields.Float(string = 'Quantity', required=True, default=1)
    account_id = fields.Many2one('account.account', 'Account', required=True)
    taxes_id = fields.Many2many('account.tax', 'product__line_taxes_rel', 'prod_line_id', 'tax_id', 'Sale Taxes', domain=[('parent_id','=',False), ('type_tax_use','in',['sale','all'])])
    

class pricelist(models.Model):
    '''Product pricelist'''
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    @api.multi
    def price_get(self, prod_id, qty, partner=None):
        '''
        self.env.context = {
            'uom': Unit of Measure (int),
            'partner': Partner ID (int),
            'date': Date of the pricelist (%Y-%m-%d),
        }
        '''
        Currency = self.env['res.currency']
        Product = self.env['product.product']
        Supplierinfo = self.env['product.supplierinfo']
        PriceType = self.env['product.price.type']

        product = Product.browse(prod_id)
        context = self.env.context.copy()
        if 'partner_id' in context:
            partner = context['partner_id']
        context['partner_id'] = partner

        date = time.strftime('%Y-%m-%d')
        if context and ('date' in context):
            date = context['date']

        result = {}
        for id in self.ids:
            self.env.cr.execute('SELECT * ' \
                    'FROM product_pricelist_version ' \
                    'WHERE pricelist_id = %s AND active=True ' \
                        'AND (date_start IS NULL OR date_start <= %s) ' \
                        'AND (date_end IS NULL OR date_end >= %s) ' \
                    'ORDER BY id LIMIT 1', (id, date, date))
            plversion = self.env.cr.dictfetchone()

            if not plversion:
                raise Warning(_('Warning !'),
                              _('No active version for the selected pricelist !\nPlease create or activate one.'))

            self.env.cr.execute('SELECT id, categ_id ' \
                    'FROM product_template ' \
                    'WHERE id = (SELECT product_tmpl_id ' \
                        'FROM product_product ' \
                        'WHERE id = %s)', (prod_id,))
            tmpl_id, categ = self.env.cr.fetchone()
            categ_ids = []
            while categ:
                categ_ids.append(str(categ))
                self.env.cr.execute('SELECT parent_id ' \
                        'FROM product_category ' \
                        'WHERE id = %s', (categ,))
                categ = self.env.cr.fetchone()[0]
                if str(categ) in categ_ids:
                    raise Warning(_('Warning !'),
                                  _('Could not resolve product category, you have defined cyclic categories of products!'))
            if categ_ids:
                categ_where = '(categ_id IN (' + ','.join(categ_ids) + '))'
            else:
                categ_where = '(categ_id IS NULL)'

            self.env.cr.execute(
                'SELECT i.*, pl.currency_id '
                'FROM product_pricelist_item AS i, '
                    'product_pricelist_version AS v, product_pricelist AS pl '
                'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                    'AND (product_id IS NULL OR product_id = %s) '
                    'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                    'AND price_version_id = %s '
                    'AND (min_quantity IS NULL OR min_quantity <= %s) '
                    'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                'ORDER BY sequence LIMIT 1',
                (tmpl_id, prod_id, plversion['id'], qty))
            res = self.env.cr.dictfetchone()
            if res:
                if res['base'] == -1:
                    if not res['base_pricelist_id']:
                        price = 0.0
                    else:
                        base_pricelist = self.browse(res['base_pricelist_id'])
                        price_tmp = base_pricelist.price_get(prod_id, qty)[res['base_pricelist_id']]
                        price = base_pricelist.currency_id.compute(price_tmp, Currency.browse(res['currency_id']), round=False)
                elif res['base'] == -2:
                    where = []
                    if partner:
                        where = [('name', '=', partner)]
                    sinfo = Supplierinfo.search([('product_id', '=', tmpl_id)] + where)
                    price = 0.0
                    if sinfo:
                        self.env.cr.execute('SELECT * ' \
                                'FROM pricelist_partnerinfo ' \
                                'WHERE suppinfo_id IN (' + \
                                    ','.join(map(str, sinfo)) + ') ' \
                                    'AND min_quantity <= %s ' \
                                'ORDER BY min_quantity DESC LIMIT 1', (qty,))
                        res2 = self.env.cr.dictfetchone()
                        if res2:
                            price = res2['price']
                else:
                    price_type = PriceType.browse(int(res['base']))
                    to_curr = Currency.browse(res['currency_id'])
                    prc = product.price_get(ptype=price_type.field)[prod_id]
                    price = price_type.currency_id.compute(prc, to_curr)
                price_limit = price
                price = price * (1.0+(res['price_discount'] or 0.0))
                # sometimes res['price_round'] will none therefore we have pass 2 for round precision
                price = rounding(price, res['price_round'] or 2)
                price += (res['price_surcharge'] or 0.0)
                if res['price_min_margin']:
                    price = max(price, price_limit+res['price_min_margin'])
                if res['price_max_margin']:
                    price = min(price, price_limit+res['price_max_margin'])
            else:
                # False means no valid line found ! But we may not raise an
                # exception here because it breaks the search
                price = False
            result[id] = price
            if context and ('uom' in context):
                uom = product.uos_id or product.uom_id
                result[id] = self.env['product.uom']._compute_price(uom.id, result[id])
        return result
     

class Product(models.Model):
    '''Product'''
    _name = 'product.product'
    _inherit = 'product.product'

    #this function will have to be corrected in order to match the criteria grid of the CCI
    @api.multi
    def price_get(self,ptype='list_price'):
        res = {}
        product_uom_obj = self.env['product.uom']
        # force_member works for forcing member price if partner is non member, same reasonning for force_non_member
        for product in self: #self.browse(cr, uid, ids, context=context):
       #     import pdb; pdb.set_trace()
            partner_status = self.env.context.get('partner_id') and self.env['res.partner'].browse(self.env.context.get('partner_id')).membership_state or False
            if ptype == 'member_price' or partner_status in  ['waiting','associated','free','paid','invoiced']:
                res[product.id] = product['list_price']
#                 if self.env.context and ('partner_id' in self.env.context):
#                     state = partner_status 
#                     if (state in ['waiting','associated','free','paid','invoiced']):
#                         res[product.id] = product['member_price']
#                 if self.env.context and ('force_member' in self.env.context):
#                     if self.env.context['force_member']:
#                         res[product.id] = product['member_price']
                if self.env.context and ('force_non_member' in self.env.context):
                    if self.env.context['force_non_member']:
                        res[product.id] = product['list_price']
            else:
                res[product.id] = product[ptype] or 0.0
                if ptype == 'list_price':
#                     res[product.id] = (res[product.id] * (product.price_margin or 1.0) ) + \
#                             product.price_extra
                    res[product.id] = res[product.id] + product.price_extra
            if 'uom' in self.env.context:
                uom = product.uos_id or product.uom_id
                res[product.id] = product_uom_obj.with_context(self.env.context)._compute_price(uom.id, res[product.id])
          
        for product in self: #self.browse(cr, uid, ids, context=context):
            #change the price only for ATA originals
            if product.name.find('ATA - original') != -1:
                if self.env.context and ('value_goods' in self.env.context):
                    if self.env.context['value_goods'] < 25000:
                        res[product.id] = res[product.id] + self.env.context['value_goods']*0.0084
                    elif 25000 <= self.env.context['value_goods'] < 75000 :
                        res[product.id] = res[product.id] + self.env.context['value_goods']*0.00655
                    elif 75000 <= self.env.context['value_goods'] < 250000 :
                        res[product.id] = res[product.id] + self.env.context['value_goods']*0.00419
                    else:
                        res[product.id] = res[product.id] + self.env.context['value_goods']*0.00261
                if self.env.context and ('double_signature' in self.env.context):
                    if self.env.context['double_signature'] == False:
                        res[product.id] = res[product.id] + 5.45
  
            #change the price only for warranty own risk on ATA carnet
            if product.name.find('ATA - Garantie Risque Propre') != -1:
                if self.env.context and ('value_goods' in self.env.context):
                    if self.env.context['value_goods'] > 15000:
                        res[product.id] = round(self.env.context['value_goods']*0.03)
  
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


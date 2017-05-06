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

from openerp import models, fields , api , _

import time
import datetime


STATE = [
    ('none', 'Non Member'),
    ('canceled', 'Canceled Member'),
    ('old', 'Old Member'),
    ('waiting', 'Waiting Member'),
    ('invoiced', 'Invoiced Member'),
    ('free', 'Free Member'),
    ('paid', 'Paid Member'),
]

#STATE_PRIOR is not used anywhere on Odoo8 but its defined in 
#            base module 'membership' with less values, so we redefine it here 
#            just for the case someone used it in module inheriting of this one
STATE_PRIOR = {
        'none' : 0,
        'canceled' : 1,
        'old' : 2,
        'waiting' : 3,
        'invoiced' : 4,
        'free' : 6,
        'paid' : 7
        }

class membership_line(models.Model):
    _inherit = 'membership.membership_line'

    @api.multi
    def state(self):
        '''Compute the state lines'''
        # this method replaces the super() method because we want to change to status of invoice partially
        # paid via a out_refund : the invoice is considered as paid and not more canceled by the partial out_refund
        for line in self:
            self.env.cr.execute('''
            SELECT i.state, i.id FROM
            account_invoice i 
            WHERE
            i.id = (
                SELECT l.invoice_id FROM
                account_invoice_line l WHERE
                l.id = (
                    SELECT  ml.account_invoice_line FROM
                    membership_membership_line ml WHERE
                    ml.id = %s
                    )
                )
            ''', (line.id,))
            fetched = self.env.cr.fetchone()
            if not fetched :
                line.state = 'canceled'
                continue
            istate = fetched[0]
            state = 'none'
            if (istate == 'draft') | (istate == 'proforma'):
                state = 'waiting'
            elif istate == 'open':
                state = 'invoiced'
            elif istate == 'paid':
                state = 'paid'
                inv = self.env['account.invoice'].browse(fetched[1])
                out_refund = other = False
                for payment in inv.payment_ids:
                    if payment.invoice and payment.invoice.type == 'out_refund':
                        out_refund = True
                    else:
                        other = True
                if out_refund and not other:
                    state = 'canceled'
            elif istate == 'cancel':
                state = 'canceled'
            line.state = state

    subtotal = fields.Float(related = 'account_invoice_line.price_subtotal', string='Subtotal', readonly=True)
    invoice_id = fields.Many2one(related = 'account_invoice_line.invoice_id', string='Account', relation='account.invoice', readonly=True)
    number = fields.Char(related = 'invoice_id.number', string='Invoice Number',readonly=True)
    date_invoice = fields.Date(related = 'invoice_id.date_invoice', string="Date Invoiced", readonly=True)
    state = fields.Selection(compute='state',  string='State', selection=STATE)

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner'


    @api.model
    def _membership_state8(self, partner_ids):
        today = time.strftime('%Y-%m-%d')
        res = {}
        partners = self.env['res.partner'].browse(partner_ids)
        for partner in partners:
            res[partner.id] = 'none'
            if (not partner.status_id.in_activity) or (not partner.active):
                continue
            if partner.refuse_membership:
                res[partner.id] = 'canceled'
                continue
            if partner.free_member:
                res[partner.id] = 'free'
                continue
            s = 'none'
            if partner.member_lines:
                for mline in partner.member_lines:
                    if mline.date_from <= today and mline.date_to >= today and mline.account_invoice_line and mline.account_invoice_line.invoice_id and mline.account_invoice_line.invoice_id.type == 'out_invoice':
                        mstate = mline.account_invoice_line.invoice_id.state
                        if mstate == 'paid':
                            if mline.state == 'canceled':
                                if s!='paid' and s!='invoiced':
                                    s = 'canceled'
                            else:
                                s = 'paid'
                                break
                        elif mstate == 'open' and s!='paid':
                            s = 'invoiced'
                        elif mstate == 'cancel' and s!='paid' and s!='invoiced':
                            s = 'canceled'
                        elif  (mstate == 'draft' or mstate == 'proforma') and s!='paid' and s!='invoiced':
                            s = 'waiting'
                if s=='none':
                    for mline in partner.member_lines:
                        if mline.date_from < today and mline.date_to < today and mline.date_from<=mline.date_to and mline.account_invoice_line and mline.account_invoice_line.invoice_id.state == 'paid' and mline.account_invoice_line.invoice_id.type == 'out_invoice' and mline.state == 'paid':
                            s = 'old'
                        else:
                            s = 'none'
                res[partner.id] = s
            if partner.associate_member and res[partner.id] not in ('paid','invoiced','waiting'):
                res_state = self._membership_state8([partner.associate_member.id])
                res[partner.id] = res_state[partner.associate_member.id]
        return res

#    @api.v7
    def _membership_state(self, cr, uid, ids, name, args=None, context=None):
        #the call to super is deactivated because of unresolved conflicts with the 5.0 version
        #of the membership module in state priorities. It is replaced by the ugly copy/paste below
        #res = super(res_partner, self)._membership_state(cr, uid, ids, name, args, context)
        res = {}
        for id in ids:
            res[id] = 'none'
        today = time.strftime('%Y-%m-%d')
        for id in ids:
            partner_data = self.browse(cr,uid,id)
            # commented by Philmer - the membership_cancel field is always filled if there is only one membership_line
            # with a date_cancel even if there is more membership_line more recent not canceled
            #if partner_data.membership_cancel and today > partner_data.membership_cancel:
            #    res[id] = 'canceled'
            #    continue
            if not partner_data.status_id.in_activity or not partner_data.active:
                res[id] = 'none'
                continue
            if partner_data.refuse_membership:
                res[id] = 'canceled'
                continue
            if partner_data.free_member:
                res[id] = 'free'
                continue
            s = 4
            if partner_data.member_lines:
                for mline in partner_data.member_lines:
                    if mline.date_from <= today and mline.date_to >= today and mline.account_invoice_line and mline.account_invoice_line.invoice_id and mline.account_invoice_line.invoice_id.type == 'out_invoice':
                            mstate = mline.account_invoice_line.invoice_id.state
                            if mstate == 'paid':
                                if mline.state == 'canceled':
                                    if s!=0 and s!=1:
                                        s = 2
                                else:
                                    s = 0
                                    break
                            elif mstate == 'open' and s!=0:
                                s = 1
                            elif mstate == 'cancel' and s!=0 and s!=1:
                                s = 2
                            elif  (mstate == 'draft' or mstate == 'proforma') and s!=0 and s!=1:
                                s = 3
                if s==4:
                    for mline in partner_data.member_lines:
                        if mline.date_from < today and mline.date_to < today and mline.date_from<=mline.date_to and mline.account_invoice_line and mline.account_invoice_line.invoice_id.state == 'paid' and mline.account_invoice_line.invoice_id.type == 'out_invoice' and mline.state == 'paid':
                            s = 5
                        else:
                            s = 6
                if s==0:
                    res[id] = 'paid'
                elif s==1:
                    res[id] = 'invoiced'
                elif s==2:
                    res[id] = 'canceled'
                elif s==3:
                    res[id] = 'waiting'
                elif s==5:
                    res[id] = 'old'
                elif s==6:
                    res[id] = 'none'
            if partner_data.associate_member and res[id] not in ('paid','invoiced','waiting'):
                res_state = self._membership_state(cr, uid, [partner_data.associate_member.id], name, args, context)
                res[id] = res_state[partner_data.associate_member.id]
        return res

    @api.model
    def _membership_state_job8(self, temp=''):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        partners = self.env['res.partner'].search([('parent_id','=',False),('is_company','=',True),'|',('active','=',True),('active','=',False)])
        changed_lines = []
        for partner in partners:
            new_mstates = partner._membership_state8([partner.id,])
            new_mstate = new_mstates[partner.id]
            if new_mstate != partner.membership_state:
                # record the change
                changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner.name, str(partner.id),partner.membership_state or '',new_mstate) )
                partner.membership_state = new_mstate
            if ( not partner.cci_date_start_membership ) and ( not partner.cci_date_stop_membership ) and new_mstate in ('paid','free','invoiced'):
                # new member today
                partner.cci_date_start_membership = today
            elif ( partner.cci_date_start_membership ) and ( not partner.cci_date_stop_membership ) and new_mstate not in ('paid','free','invoiced'):
                # old member today
                partner.cci_date_stop_membership = today
            elif ( partner.cci_date_start_membership ) and ( partner.cci_date_stop_membership ) and new_mstate in ('paid','free','invoiced'):
                # member today again
                partner.cci_date_stop_membership = False
            elif ( partner.cci_date_start_membership ) and ( partner.cci_date_stop_membership ) and (partner.cci_date_start_membership >= partner.cci_date_stop_membership) and new_mstate not in ('paid','free','invoiced'):
                # non member today again
                partner.cci_date_stop_membership = today
        if changed_lines:
            final_text = u'Changements hebdomadaires : \n' + ( u'\n'.join( changed_lines ) )
        else:
            final_text = u"Changements hebdomadaires : aucun"
        membership_check_obj = self.pool.get('cci_membership.membership_check')
        id = self.env['cci_membership.membership_check'].create({
                        'name': datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'),
                        'count' : len(changed_lines),
                        'status': final_text,
                        })
        return True

#    @api.v7
    def _membership_state_job(self, cr, uid):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [('parent_id','=',False),('is_company','=',True),'|',('active','=','True'),('active','=','False')])
        if partner_ids:
            partners = partner_obj.read(cr, uid, partner_ids, ['id','membership_state','cci_date_start_membership','cci_date_stop_membership'] )
            new_mstates = partner_obj._membership_state(cr, uid, partner_ids, '')
            changed_lines = []
            for partner in partners:
                if new_mstates.has_key( partner['id'] ):
                    if partner['membership_state'] <> new_mstates[partner['id']]:
                        # record the change
                        partner_name = partner_obj.read(cr, uid, [partner['id']], ['name'] )[0]['name']
                        changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner_name, str(partner['id']),partner['membership_state'],new_mstates[partner['id']]) )
                        partner_obj.write(cr, uid, [partner['id']], {'membership_state':new_mstates[partner['id']]} )
                    if ( not partner['cci_date_start_membership'] ) and ( not partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] in ('paid','free','invoiced'):
                        # new member today
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_start_membership':today} )
                    elif ( partner['cci_date_start_membership'] ) and ( not partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] not in ('paid','free','invoiced'):
                        # old member today
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_stop_membership':today} )
                    elif ( partner['cci_date_start_membership'] ) and ( partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] in ('paid','free','invoiced'):
                        # member today again
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_stop_membership':False} )
                    elif ( partner['cci_date_start_membership'] ) and ( partner['cci_date_stop_membership'] ) and (partner['cci_date_start_membership'] >= partner['cci_date_stop_membership']) and new_mstates[partner['id']] not in ('paid','free','invoiced'):
                        # non member today again
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_stop_membership':today} )
            if changed_lines:
                final_text = u'Changements hebdomadaires : \n' + ( u'\n'.join( changed_lines ) )
            else:
                final_text = u"Changements hebdomadaires : aucun"
            membership_check_obj = self.pool.get('cci_membership.membership_check')
            id = membership_check_obj.create(cr, uid, {
                'name': datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'),
                'count' : len(changed_lines),
                'status': final_text,
                })
        return True

    @api.multi
    def _membership_vcs(self):
        '''To obtain the ID of the partner in the form of a belgian VCS for a membership offer'''
        for rec in self:
            value_digits = 1000000000 + rec.id
            check_digits = value_digits % 97
            if check_digits == 0:
                check_digits = 97
            pure_string = str(value_digits) + ( str(check_digits).zfill(2) )
            rec.membership_vcs = '***' + pure_string[0:3] + '/' + pure_string[3:7] + '/' + pure_string[7:] + '***'

    @api.onchange('membership_explanation')
    def onchange_membership_explanation(self):
        if self.membership_explanation:
            self.read_before_next_membership_bill = True
        else:
            self.read_before_next_membership_bill = False

    membership_vcs = fields.Char(compute='_membership_vcs',string='VCS number for membership offer',size=20)
    refuse_membership = fields.Boolean('Refuse to Become a Member',default=False)
    membership_explanation = fields.Text('Membership Explanation',help='Here you can explain the amount asked or the special treatment for the membership of this partner')
    membership_first_year = fields.Char('First Year of membership',help='To manually give the first year of membership',size=4)
    desc_add_site = fields.Char('Explanation of additional sites',help='Text inserted on invoice to explain the number of additional sites',size=200)
    cci_date_start_membership = fields.Date('Start of Membership',help='Date of first membership') ### first date of membership. Doesn't change if become non member or new member again
    cci_date_stop_membership = fields.Date('End of Membership',help='Last date of membership loss')  ### last date of becoming non-member
    next_membership_bill_forced = fields.Boolean('Force the next automatic bill',help="The next time we'll use the automatic bill or call for membreship, this partner will be taken into account")
    read_before_next_membership_bill = fields.Boolean('Re-read before billing',help="Selected if this text must be re-read before the next automatic billing")

class membership_check(models.Model):
    _name = 'cci_membership.membership_check'
    _description = '''Recording of a check'''
    
    name = fields.Char('Date',size=19,required=True)
    count = fields.Integer('Changes count')
    status = fields.Text('Status')

    _order = 'name desc'

class Product(models.Model):
    '''Product'''
    _inherit = 'product.template'
    _description = 'product.template'

    membership_year = fields.Integer('Membership Year', help='Year of membership concerned by this product')

class membership_range(models.Model):
    _name = 'cci_membership.membership_range'
    _description = '''Range of employees with standard membership price'''
    
    year = fields.Integer('Year',required=True)
    from_range = fields.Integer('From',help='Lower number of local employees for this range',required=True)
    to_range = fields.Integer('To',help='Upper number of employees for this range',required=True)
    amount = fields.Float('Standard amount',digits=(15,2),help='Amount to invoice by default for this range of employees')

class membership_askedused(models.Model):
    _name = 'cci_membership.membership_askedused'
    _description = '''Used asked amount of membership'''

    amount = fields.Float('Amount',digits=(15,2),readonly=True)
    count = fields.Integer('Count',readonly=True)
    total_value = fields.Float('Total Value',digits=(15,2),readonly=True)
    type_sel = fields.Char('Type of selection',size=7)

class membership_call(models.Model):
    _name = 'cci_membership.membership_call'
    _description = '''Data for calling membership'''
    
    partner_id = fields.Many2one('res.partner', string='Partner')
    address_id = fields.Many2one('res.partner', string='Address')
    job_id =  fields.Many2one('res.partner', string='Job')
    contact_id = fields.Many2one('res.partner', string='Contact')
    partner_name = fields.Char('Sending Name',size=200)
    street = fields.Char('Street',size=250)
    street2 = fields.Char('Street2',size=250)
    zip_code = fields.Char('Zip Code',size=30)
    city = fields.Char('City',size=80)
    email_addr = fields.Char('Email Address',size=200)
    phone_addr = fields.Char('Phone Address',size=50)
    fax_addr = fields.Char('Fax Address',size=50)
    name = fields.Char('Contact Name',size=120)
    first_name = fields.Char('Contact First Name',size=120)
    courtesy = fields.Char('Courtesy',size=20)
    title = fields.Char('Title',size=1000)
    title_categs = fields.Char('Categs',size=20)
    email_contact = fields.Char('Professionnal Email',size=200)
    base_amount = fields.Float('Base Amount',digits=(15,2))
    count_add_sites = fields.Integer('Additional Sites')
    unit_price_site = fields.Float('Unit Price per Site',digits=(15,2))
    desc_add_site = fields.Char('Explanation Additional Sites',size=200)
    wovat_amount = fields.Float('Invoiced Price without VAT',digits=(15,2))
    wvat_amount = fields.Float('Invoiced Price with VAT',digits=(15,2))
    salesman = fields.Char('Salesman',size=45)
    salesman_phone = fields.Char('Salesman Phone',size=45)
    salesman_fax = fields.Char('Salesman Fax',size=45)
    salesman_mobile = fields.Char('Salesman Mobile',size=45)
    salesman_email = fields.Char('Salesman Email',size=45)
    vcs = fields.Char('VCS',size=30)

class membership_by_partner(models.Model):
    _name = 'cci_membership.membership_by_partner'
    _description = '''Subtotal Membership by Partner'''

    partner_id = fields.Many2one('res.partner','Partner')
    user_id = fields.Many2one('res.users','Salesman')
    year =  fields.Integer('Membership Year')
    invoiced = fields.Float('Invoiced',digits=(15,2))
    paid = fields.Float('Paid',digits=(15,2))
    canceled = fields.Float('Canceled',digits=(15,2))
    open_value = fields.Float('Open Value',digits=(15,2))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


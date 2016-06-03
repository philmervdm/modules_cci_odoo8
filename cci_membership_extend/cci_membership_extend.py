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
from openerp import models, fields, api , _
import datetime
import time

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner'

    @api.v7
    def _membership_state(self, cr, uid, ids, name, args, context=None):
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
            if partner_data.state_id.id not in (1,) or not partner_data.active:
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
                                #TOCHECK : if paid by a credit nota : s = 2
                                # A quick way to check this is to check the state of the membership_line is 'canceled' or not
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
            #if partner_data.membership_stop and today > partner_data.membership_stop:
            #    res[id] = 'old'
            #    print 'changed to old'
            #    continue
            if partner_data.associate_member and res[id] not in ('paid','invoiced','waiting'):
                res_state = self._membership_state(cr, uid, [partner_data.associate_member.id], name, args, context)
                res[id] = res_state[partner_data.associate_member.id]
        return res

    @api.v7
    def _membership_state_job(self, cr, uid, ids=False, context={}):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, ['|',('active','=','True'),('active','=','False')], context=context)
        if partner_ids:
            partners = partner_obj.read(cr, uid, partner_ids, ['id','membership_state','cci_date_start_membership','cci_date_stop_membership'] )
            new_mstates = partner_obj._membership_state(cr, uid, partner_ids, '', args=None, context=None)
            changed_lines = []
            for partner in partners:
                if new_mstates.has_key( partner['id'] ):
                    if partner['membership_state'] <> new_mstates[partner['id']]:
                        # record the change
                        partner_name = partner_obj.read(cr, uid, [partner['id']], ['name'] )[0]['name']
                        changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner_name, str(partner['id']),partner['membership_state'],new_mstates[partner['id']]) )
                        partner_obj.write(cr, uid, [partner['id']], {}, context )
                    if ( not partner['cci_date_start_membership'] ) and ( not partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] in ('paid','free','invoiced'):
                        # new member today
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_start_membership':today}, context )
                    elif ( partner['cci_date_start_membership'] ) and ( not partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] not in ('paid','free','invoiced'):
                        # old member today
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_stop_membership':today}, context )
                    elif ( partner['cci_date_start_membership'] ) and ( partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] in ('paid','free','invoiced'):
                        # member today again
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_stop_membership':False}, context )
                    elif ( partner['cci_date_start_membership'] ) and ( partner['cci_date_stop_membership'] ) and (partner['cci_date_start_membership'] >= partner['cci_date_stop_membership']) and new_mstates[partner['id']] not in ('paid','free','invoiced'):
                        # non member today again
                        partner_obj.write(cr, uid, [partner['id']], {'cci_date_stop_membership':today}, context )
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
    
    
#     @api.multi
#     def _membership_state_job(self):
#         today = datetime.datetime.today().strftime('%Y-%m-%d')
#         partner_obj = self.env['res.partner']
#         partner_ids = partner_obj.search(['|',('active','=','True'),('active','=','False')])
#         if partner_ids:
#             partners = partner_ids.read(['id','membership_state','cci_date_start_membership','cci_date_stop_membership'] )
#             new_mstates = partner_ids._membership_state()
#             changed_lines = []
#             for partner in partners:
#                 partner_brws = partner_obj.browse(partner['id'])
#                  
#                 if new_mstates.has_key( partner['id'] ):
#                     if partner['membership_state'] <> new_mstates[partner['id']]:
#                         # record the change
#                         partner_name = partner_brws.name
#                         changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner_name, str(partner['id']),partner['membership_state'],new_mstates[partner['id']]) )
#                         partner_brws.write({})
#                     if ( not partner['cci_date_start_membership'] ) and ( not partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] in ('paid','free','invoiced'):
#                         # new member today
#                         partner_brws.write({'cci_date_start_membership':today})
#                     elif ( partner['cci_date_start_membership'] ) and ( not partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] not in ('paid','free','invoiced'):
#                         # old member today
#                         partner_brws.write({'cci_date_stop_membership':today})
#                     elif ( partner['cci_date_start_membership'] ) and ( partner['cci_date_stop_membership'] ) and new_mstates[partner['id']] in ('paid','free','invoiced'):
#                         # member today again
#                         partner_brws.write({'cci_date_stop_membership':False})
#                     elif ( partner['cci_date_start_membership'] ) and ( partner['cci_date_stop_membership'] ) and (partner['cci_date_start_membership'] >= partner['cci_date_stop_membership']) and new_mstates[partner['id']] not in ('paid','free','invoiced'):
#                         # non member today again
#                         partner_brws.write({'cci_date_stop_membership':today})
#              
#             if changed_lines:
#                 final_text = u'Changements hebdomadaires : \n' + ( u'\n'.join( changed_lines ) )
#             else:
#                 final_text = u"Changements hebdomadaires : aucun"
#                  
#             membership_check_obj = self.env['cci_membership.membership_check']
#             id = membership_check_obj.create({
#                 'name': datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'),
#                 'count' : len(changed_lines),
#                 'status': final_text,
#                 })
#         return True
    
    @api.onchange('membership_explanation')
    def onchange_membership_explanation(self):
        if self.membership_explanation:
            self.read_before_next_membership_bill = True
        else:
            self.read_before_next_membership_bill = False

    site_membership = fields.Integer('Additional sites for membership', default=0)
    desc_add_site = fields.Char('Explanation of additional sites',help='Text inserted on invoice to explain the number of additional sites',size=200)
    cci_date_start_membership = fields.Date('Start of Membership',help='Date of first membership') ### first date of membership. Doesn't change if become non member or new member again
    cci_date_stop_membership = fields.Date('End of Membership',help='Last date of membership loss')  ### last date of becoming non-member
    next_membership_bill_forced = fields.Boolean('Force the next automatic bill',help="The next time we'll use the automatic bill or call for membreship, this partner will be taken into account")
    read_before_next_membership_bill = fields.Boolean('Re-read before billing',help="Selected if this text must be re-read before the next automatic billing")


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
    type = fields.Char('Type of selection',size=7)

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
    open = fields.Float('Open',digits=(15,2))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import datetime

PROD_CODES = {
    'AE':1,
    'CCIMAG':14,
    'CNN':13,
    'EMPL':5,
    'EVENT':4,
    'MEMB':8,
    'MILN':16,
    'REP':15,
    'SPONS':9,
    'TABLE':2,
}

ACTIONS = [
    ('appel_sortant','Appel sortant'),
    ('appel_entrant','Appel entrant'),
    ('commando','Commando'),
    ('mail','Mail'),
    ('site','Site Internet'),
    ('meeting_cci','Meeting CCI'),
    ('meeting_externe','Meeting externe'),
    ('midi','Midi'),
    ('rdv','RDV'),
]

class create_interests(models.TransientModel):
    
    _name = 'create.interests'
    
    partner_id = fields.Many2one('res.partner', string='Partner', required = True)
    ae = fields.Boolean(string='AE')
    ae_subproduct = fields.Many2one('cci.product.category', string ='Sous-produit', domain= "[('cci_product.code','=',%s)]" % PROD_CODES['AE'])
    ae_date = fields.Date(string='Date')
    ae_comment = fields.Char(string='Comment')
    ae_job_id = fields.Many2one('res.partner', string = 'Contact Partner', domain = "[('contact_id','=',partner_id)]")
    ccimag = fields.Boolean(string='CCI Mag')
    ccimag_subproduct = fields.Many2one('cci.product.category', string = 'Sous-produit', domain="[('cci_product.code','=',%s)]" % PROD_CODES['CCIMAG'])
    ccimag_date = fields.Date(string='Date')
    ccimag_comment = fields.Char(string = 'Comment')
    ccimag_job_id = fields.Many2one('res.partner', string = 'Contact Partner', domain = "[('contact_id','=',partner_id)]")
    cnn = fields.Boolean(string='CNN')
    cnn_subproduct = fields.Many2one('cci.product.category', string='Sous-produit', domain="[('cci_product.code','=',%s)]" % PROD_CODES['CNN'])
    cnn_date = fields.Date(string='Date')
    cnn_comment = fields.Char(string='Comment')
    cnn_job_id = fields.Many2one('res.partner', string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    empl = fields.Boolean(string='Employeur')
    empl_subproduct= fields.Many2one('cci.product.category', string='Sous-produit', domain = "[('cci_product','=',%s)]" % PROD_CODES['EMPL'])
    empl_date=fields.Date(string='Date')
    empl_comment = fields.Char(string ='Comment')
    empl_job_id = fields.Many2one('res.partner', string = 'Contact Partner', domain="[('contact_id','=',partner_id)]")
    event = fields.Boolean(string='Event')
    event_subproduct = fields.Many2one('cci.product.category', string ='Sous-produit', domain="[('cci_product','=',%s)]" % PROD_CODES['EVENT'])
    event_date = fields.Date(string ='Date')
    event_comment = fields.Char(string='Comment')
    event_job_id = fields.Many2one('res.partner', string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    memb = fields.Boolean(string='MEMB')
    memb_subproduct = fields.Many2one('cci.product.category', string='Sous-produit', domain="[('cci_product','=',%s)]" % PROD_CODES['MEMB'])
    memb_date = fields.Date(string='Date')
    memb_comment = fields.Char(string='Comment')
    memb_job_id = fields.Many2one('res.partner', string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    mi = fields.Boolean(string='MeetIN')
    mi_subproduct = fields.Many2one('cci.product.category', string='Sous-produit', domain ="[('cci_product','=',%s)]" % PROD_CODES['MILN'])
    mi_date = fields.Date(string ='Date')
    mi_comment = fields.Char(string='Comment')
    mi_job_id = fields.Many2one('res.partner', string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    rep = fields.Boolean(string ='REP')
    rep_subproduct = fields.Many2one('cci.product.category', string='Sous-produit', domain = "[('cci_product','=',%s)]" % PROD_CODES['REP'])
    rep_date = fields.Date(string='Date')
    rep_comment = fields.Char(string ='Comment')
    rep_job_id = fields.Many2one('res.partner', string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    spons = fields.Boolean(string='Sponsoring')
    spons_subproduct = fields.Many2one('cci.product.category', string= 'Sous-produit',domain="[('cci_product','=',%s)]" % PROD_CODES['SPONS'])
    spons_date = fields.Date(string='Date')
    spons_comment =fields.Char(string='Comment')
    spons_job_id = fields.Many2one('res.partner',string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    table = fields.Boolean(string='Table')
    table_subproduct = fields.Many2one('cci.product.category', string='Sous-produit',domain="[('cci_product','=',%s)]" % PROD_CODES['TABLE'])
    table_date = fields.Date(string='Date')
    table_comment = fields.Char(string = 'Comment')
    table_job_id = fields.Many2one('res.partner',string='Contact Partner',domain="[('contact_id','=',partner_id)]")
    histo = fields.Boolean(string='Historique')
    histo_action = fields.Selection(ACTIONS, string='Action')
    histo_product = fields.Many2one('cci.product', string='Produit')
    histo_subproduct = fields.Many2one('cci.product.category', string='Sous-produit', domain ="[('cci_product','=',histo_product)]")
    histo_comment = fields.Char(string='Comment')
    histo_job_id = fields.Many2one('res.partner', string='Contact Partner', domain="[('contact_id','=',partner_id)]")
    
    @api.model
    def get_defaults(self, data):
        pool = pooler.get_pool(cr.dbname)
        current_partner_id = False
        if data['model'] == 'res.partner.history':
            hist_obj = self.env['res.partner.history']
            histo = hist_obj.browse(data['id'])
            if histo.partner:
                current_partner_id = histo.partner.id
        elif data['model'] == 'res.partner.interest':
            int_obj = self.env['res.partner.interest']
            interest = int_obj.browse(data['id'])
            if interest.partner:
                current_partner_id = interest.partner.id
        elif data['model'] == 'crm_cci.todo':
            todo_obj = self.env['crm_cci.todo']
            todo = todo_obj.browse(data['id'])
            if todo.partner:
                current_partner_id = todo.partner.id
        elif data['model'] == 'res.partner':
            current_partner_id = data['id']
        if current_partner_id:
            fields['partner_id']['default'] = current_partner_id
        return data['form']

    @api.multi
    def create_interestmarks(self):
        # search the cci.contact from uid
        interest_obj = self.env['res.partner.interest']
        cci_contact_obj = self.env['cci.contact']
        cci_contacts = cci_contact_obj.search([('user','=',self.env.uid)])
        cci_product_obj = self.env['cci.product']
        new_interest_ids = []
        if cci_contacts and self.partner_id:
            cci_contact = cci_contacts[0]
            new_interest = {
                'cci_contact_follow' : self.env.uid,
                'date': datetime.datetime.today().strftime('%Y-%m-%d'),
                'cci_contact' : cci_contact.id,
                'partner' : self.partner_id.id,
            }
            if self.ae:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['AE'])]).id
                if self.ae_subproduct:
                    new_subproduct = self.ae_subproduct.id
                else:
                    new_subproduct = False
                if self.ae_date:
                    new_date = self.ae_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.ae_job_id:
                    new_contact = self.ae_job_id
                else:
                    new_contact = False
                if self.ae_comment:
                    new_desc = self.ae_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.ccimag:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['CCIMAG'])]).id
                if self.ccimag_subproduct:
                    new_subproduct = self.ccimag_subproduct.id
                else:
                    new_subproduct = False
                if self.ccimag_date:
                    new_date = self.ccimag_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.ccimag_job_id:
                    new_contact = self.ccimag_job_id
                else:
                    new_contact = False
                if self.ccimag_comment:
                    new_desc = self.ccimag_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.cnn:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['CNN'])]).id
                if self.cnn_subproduct:
                    new_subproduct = self.cnn_subproduct.id
                else:
                    new_subproduct = False
                if self.cnn_date:
                    new_date = self.cnn_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.cnn_job_id:
                    new_contact = self.cnn_job_id
                else:
                    new_contact = False
                if self.cnn_comment:
                    new_desc = dcnn_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.empl:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['EMPL'])]).id
                if self.empl_subproduct:
                    new_subproduct = self.empl_subproduct.id
                else:
                    new_subproduct = False
                if self.empl_date:
                    new_date = self.empl_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.empl_job_id:
                    new_contact = self.empl_job_id
                else:
                    new_contact = False
                if self.empl_comment:
                    new_desc = self.empl_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.event:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['EVENT'])]).id
                if self.event_subproduct:
                    new_subproduct = self.event_subproduct.id
                else:
                    new_subproduct = False
                if self.event_date:
                    new_date = self.event_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.event_job_id:
                    new_contact = self.event_job_id
                else:
                    new_contact = False
                if self.event_comment:
                    new_desc = self.event_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.memb:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['MEMB'])]).id
                if self.memb_subproduct:
                    new_subproduct = self.memb_subproduct.id
                else:
                    new_subproduct = False
                if self.memb_date:
                    new_date = self.memb_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.memb_job_id:
                    new_contact = self.memb_job_id
                else:
                    new_contact = False
                if self.memb_comment:
                    new_desc = self.memb_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(cr,uid,new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.mi:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['MILN'])]).id
                if self.mi_subproduct:
                    new_subproduct = self.mi_subproduct.id
                else:
                    new_subproduct = False
                if self.mi_date:
                    new_date = self.mi_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.mi_job_id:
                    new_contact = self.mi_job_id
                else:
                    new_contact = False
                if self.mi_comment:
                    new_desc = self.mi_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.rep:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['REP'])]).id
                if self.rep_subproduct:
                    new_subproduct = self.rep_subproduct.id
                else:
                    new_subproduct = False
                if self.rep_date:
                    new_date = self.rep_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.rep_job_id:
                    new_contact = self.rep_job_id
                else:
                    new_contact = False
                if self.rep_comment:
                    new_desc = self.rep_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.spons:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['SPONS'])]).id
                if self.spons_subproduct:
                    new_subproduct = self.spons_subproduct.id
                else:
                    new_subproduct = False
                if self.spons_date:
                    new_date = self.spons_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.spons_job_id:
                    new_contact = self.spons_job_id
                else:
                    new_contact = False
                if self.spons_comment:
                    new_desc = self.spons_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.table:
                new_data = new_interest.copy()
                new_product = cci_product_obj.search([('code','=',PROD_CODES['TABLE'])]).id
                if self.table_subproduct:
                    new_subproduct = self.table_subproduct.id
                else:
                    new_subproduct = False
                if self.table_date:
                    new_date = self.table_date
                else:
                    new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.table_job_id:
                    new_contact = self.table_job_id
                else:
                    new_contact = False
                if self.table_comment:
                    new_desc = self.table_comment
                else:
                    new_desc = '-'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,'description':new_desc})
                result_id = interest_obj.create(new_data)
                if result_id:
                    new_interest_ids.append(result_id)
            if self.histo and self.histo_action:
                new_data = new_interest.copy()
                new_action = self.histo_action
                if self.histo_product:
                    new_product = self.histo_product.id
                else:
                    new_product = False
                if self.histo_product and self.histo_subproduct:
                    new_subproduct = self.histo_subproduct.id
                else:
                    new_subproduct = False
                new_date = datetime.datetime.today().strftime('%Y-%m-%d')
                if self.histo_job_id:
                    new_contact = self.histo_job_id
                else:
                    new_contact = False
                if self.histo_comment:
                    new_desc = self.histo_comment
                else:
                    new_desc = '-'
                other_descs = []
                if self.ae_comment:
                    other_descs.append(self.ae_comment)
                if self.ccimag_comment:
                    other_descs.append(self.ccimag_comment)
                if self.cnn_comment:
                    other_descs.append(self.cnn_comment)
                if self.empl_comment:
                    other_descs.append(self.empl_comment)
                if self.event_comment:
                    other_descs.append(self.event_comment)
                if self.memb_comment:
                    other_descs.append(self.memb_comment)
                if self.mi_comment:
                    other_descs.append(self.mi_comment)
                if self.rep_comment:
                    other_descs.append(self.rep_comment)
                if self.spons_comment:
                    other_descs.append(self.spons_comment)
                if self.table_comment:
                    other_descs.append(self.table_comment)
                if other_descs:
                    if new_desc != '-':
                        new_desc = new_desc.strip() + ',' + ','.join([x.strip() for x in other_descs])
                    else:
                        new_desc = ','.join([x.strip() for x in other_descs])
                new_state = 'closed'
                new_data.update({'product':new_product,'category':new_subproduct,'next_action':new_date,
                                 'contact':new_contact,'description':new_desc,'action':new_action,'state':new_state})
                result_id = self.env['res.partner.history'].create(new_data)
        return True
    
#     states = {
#         'init': {
#             'actions': [_get_defaults],
#             'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancel'),('create','Create')]},
#         },
#         'create': {
#             'actions': [],
#             'result': {'type': 'action', 'action': create_interestmarks, 'state': 'end'}
#         }
#     }
#     
# create_interests('create_interests')

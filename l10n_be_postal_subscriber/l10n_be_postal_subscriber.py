# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (c) 2009 CCI  ASBL. (<http://www.ccilconnect.be>).
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
import time

class res_partner_state(models.Model):
    _name = "res.partner.state"
    _description = 'res.partner.state'

    name = fields.Char(string= 'Partner Status', required=True)

class res_partner(models.Model):
    _inherit = "res.partner"
    
    @api.model
    def _get_partner_state(self):
        ids = self.env['res.partner.state'].search([('name','like', 'En Activité')], limit=1)
        return ids


    activ_state_id = fields.Many2one('res.partner.state', string = 'Partner State',help='status of activity of the partner', default=_get_partner_state)
    magazine_subscription = fields.Selection( [('never','Never'),('prospect','Prospect'),('personal','Personal'), ('postal','Postal')], string="Magazine subscription", default = 'prospect')
    magazine_subscription_source = fields.Char(string = 'Mag. Subscription Source')


class dated_photo(models.Model):
    '''A photo of some details about partner's addresses and contacts at a precise date'''
    _name = "dated.photo"
    _description = "Photo of database at a precise date"
    
    name = fields.Char(string = 'Name', required=True, default = 'Photo ' + time.strftime('%d-%m-%Y %H:%M:%S'))
    datetime = fields.Datetime('Date', required=True, readonly=True, default=fields.Date.context_today)
    photo_details_ids = fields.One2many('photo.detail', 'photo_id', string='Postal subscribers', )
    
    @api.model
    def create(self, vals):
        temp = super(dated_photo,self).create(vals)
        self._take_one_shoot(temp)
        return temp
    
    @api.multi
    def get_all_subscriber(self):
        self.env.cr.execute( """
                    SELECT p.id as partner_id, p.name, p.title, p.state_id, p.street, p.street2, p.zip, p.city, p.type
                    FROM res_partner p WHERE p.magazine_subscription = 'postal'
                    ORDER BY p.id;
                    """)
        res = self.env.cr.fetchall()
        return res
    
    @api.multi
    def _take_one_shoot(self, photo_id):
        obj_subscriber = self.env['photo.detail']
        
        # TODO ? If we are not sure to take only one photo, at a time, we must delete all subscriber_details attached
        # before taking a new photo. Actually, only the create function of the object call this function
        # so it seems we don't need securing that point

        #Search all res.partner.address indicated as subscriber
        res = self.get_all_subscriber()

        #Record the current values of the fields copied in the SUMO DataBase
        for rec in res:
            obj_subscriber.create({
                        'photo_id': photo_id,
                        'partner_id': rec[0],
                        'partner_contact_id': False,
                        'name': rec[1],
                        'title': rec[2],
                        'activ_state_id': rec[3],
                        'address_id': rec[4],
                        'street': rec[5],
                        'street2': rec[6],
                        'zip': rec[7],
                        'city':rec[8],
                        })
        
        #Get the ID of the res_partner identifying the personal addresses
        obj = self.env['res.partner']
        ids = obj.search([('ref', '=', 'PERSONAL_ADDRESS' )])
        if ids:
            isolated_address_id = ids[0]
        
            #Search all res.partner.contact indicated as subscriber
            # First we extract the contacts subscriber ids
            ## TODO : perhaps, searching on the address.type = 'contact' is better than searching for the special partner_id...
            ##       if it's possible to have an address without res_partner associated (to check with Quentin)
            self.env.cr.execute( """
                    SELECT p.id as partner_id, p.name, p.street, p.street2, p.zip, a.city 
                        FROM res_partner p, WHERE c.magazine_subscription = 'postal' AND  p.id = %s and p.street != '' and p.zip != '';
                    """, isolated_address_id )
            res = self.env.cr.fetchall()
        
            #Record the current values of the fields copied in the SUMO DataBase
            #Take only the first address by order of the sequence (often the default address)
            oldID = 0
            for rec in res:
                if not rec[0] == oldID:
                 obj_subscriber.create({
                            'photo_id': self.id,
                            'partner_id': False,
                            'address_id': rec[3], 
                            'partner_contact_id': rec[0],
                            'name': rec[1]+ ' ' + rec[2],
                            'title': '',
                            'activ_state_id': '',
                            'street': rec[4],
                            'street2': rec[5],
                            'zip': rec[6],
                            'city':rec[7],
                            })
                oldID = rec[0]
    @api.multi
    def compare_with_old_photo(self, ids):
        if ids.length() == 2:
            # we search the older photo
            self.env.cr.execute( """
                        SELECT photo.id, photo.name, photo.datetime
                            FROM dated_photo photo
                            WHERE photo.id in ( %s, %s )
                            ORDER by photo.datetime;
                       """, (ids[0],ids[1]) )
            photos = self.env.cr.fetchall()
            
            self.env.cr.execute( """
                        SELECT partner_id, name, title, state_id, street, street2, zip, city
                            FROM photo_detail
                            WHERE photo_id = %s
                        """, photos[0].id )
            oldsubs = cr.fetchall()
            
            self.env.cr.execute( """
                        SELECT partner_id, name, title, state_id, street, street2, zip, city
                            FROM photo_detail
                            WHERE photo_id = %s
                        """, photos[1].id )
            newsubs = self.env.cr.fetchall()

class subscriber_photo(models.Model):
    '''Details about a res.partner.address or a res.parner.contact at a precise date. Only the details needed by the belgian software SUMO from the Post are recorded here'''
    _name = "photo.detail"
    _description = "Details about a photo of database"

    photo_id = fields.Many2one('dated.photo', string= 'Date de la photo') 
    partner_id = fields.Many2one('res.partner', string= 'Partner', help='not used if directly addressed to a person')
    name = fields.Char(string= 'Name')
    title = fields.Char(string='Title')
    activ_state_id = fields.Many2one('res.partner.state', string= 'Partner State',help='status of activity of the partner')
    street = fields.Char(string= 'Street')
    street2 = fields.Char(string= 'Street2')
    zip = fields.Char(string= 'Zip')
    city = fields.Char(string= 'City')

class photo_comparison(models.Model):
    '''Capture the sum of all differences between two photos of subscribers'''
    _name = "photo.comparison"
    _description = "comparison between 2 photos"
    
    datetime = fields.Datetime(string='Date', default=fields.Date.context_today)
    old_photo_id = fields.Many2one('dated.photo', string='Older Photo')
    new_photo_id = fields.Many2one('dated.photo', string='Newer Photo')
    diff_ids = fields.One2many('photo.diff','comparison_id', string='Found differences')

    def get_name(self):
        return 'Comparaison du ' + self.datetime.strftime('%d-%m-%Y %H-%M-%S')

class photo_diff(models.Model):
    '''Contains the result of the comparison between two states of a subscriber'''
    _name = "photo.diff"
    _description = "Details of comparison between 2 photos"

    comparison_id = fields.Many2one('photo.comparison', string= 'Comparison Date')
    type = fields.Char(string= 'Type')
    old_values = fields.Text(string= 'Anciennes valeurs')
    new_values =  fields.Text(string= 'Nouvelles valeurs')
    resource_id = fields.Integer(string= 'ID')
    model = fields.Char(string= 'DataBase')
    oldid = fields.Char(string= 'Old ID')

# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class res_partner_zip(models.Model):
    _name = 'res.partner.zip'
    _description = 'res.partner.zip'
    
    @api.constrains('groups_id')
    def check_group_type(self):
        for grp in self:
            sql = '''
            select group_id from partner_zip_group_rel1 where zip_id=%d
            ''' % (grp.id)
            self.env.cr.execute(sql)
            groups = self.env.cr.fetchall()
        list_group = []
        for group in groups:
            list_group.append(group[0])
        data_zip = self.env['res.partner.zip.group'].browse(list_group)
        list_zip = []
        for data in data_zip:
            if data.type_id.id in list_zip:
                raise Warning(_('Error: Only one group of the same group type is allowed!'))
            list_zip.append(data.type_id.id)
        return True
    
    @api.multi
    def name_get(self):
        # will return zip code and city...... perhaps country name also to see later
        if not len(self):
            return []
        res = []
        for r in self.read(['code', 'city']):
            #zip_city = str(r['code'] or '')
            #if r['code'] and r['city']:
            #    zip_city += ' '
            #r['city'] = r['city'].encode('utf-8')
            #zip_city += str(r['city'] or '')
            zip_city = ("%s %s" % ((r['code'] or '').strip(),(r['city'] or '').strip() )).strip()
            res.append((r['id'], zip_city))
        return res

    @api.model
    def distance_in_kilometers(self,zip_id1,zip_id2):
        result = False
        # get the latitude/longitude of both zip code
        if zip_id1 and zip_id2:
            zip1 = self.env['res.partner.zip'].read(zip_id1,['latitude','longitude'])
            zip2 = self.env['res.partner.zip'].read(zip_id2,['latitude','longitude'])
            if zip1 and zip2 and zip1['latitude'] and zip2['latitude'] and zip1['longitude'] and zip2['longitude']:
                lat1 = zip1['latitude']
                long1 = zip1['longitude']
                lat2 = zip2['latitude']
                long2 = zip2['longitude']

                # Convert latitude and longitude to 
                # spherical coordinates in radians.
                degrees_to_radians = math.pi/180.0
                    
                # phi = 90 - latitude
                phi1 = (90.0 - lat1)*degrees_to_radians
                phi2 = (90.0 - lat2)*degrees_to_radians
                    
                # theta = longitude
                theta1 = long1*degrees_to_radians
                theta2 = long2*degrees_to_radians
                    
                # Compute spherical distance from spherical coordinates.
                    
                # For two locations in spherical coordinates 
                # (1, theta, phi) and (1, theta, phi)
                # cosine( arc length ) = 
                #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
                # distance = rho * arc length
                
                cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
                       math.cos(phi1)*math.cos(phi2))
                arc = math.acos( cos )

                # Remember to multiply arc by the radius of the earth 
                # in your favorite set of units to get length.
                
                # * 6373 to get kilometers
                # * 3960 to get miles
                result = arc * 6373
        return result
    
    name = fields.Char('Zip Code', size=10, required=True, index=1)
    code = fields.Char('Zip Code', size=10) # required = True à ajouter une fois la migration terminée
    city = fields.Char('City', size=60, translate=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Master Cci') # to put outside, specific to CCI
    post_center_id = fields.Char('Post Center', size=40) # to delete
    post_center_special = fields.Boolean(string='Post Center Special') # to delete
    user_id = fields.Many2one('res.users', string='Salesman Responsible') # to put outside CCI specific
    groups_id = fields.Many2many('res.partner.zip.group', 'partner_zip_group_rel1', 'zip_id', 'group_id', stringe='Areas')
    distance = fields.Integer(string='Distance', help='Distance (km) between zip location and the cci.') # to delete
    old_city = fields.Char(string='Old City Name', size=60) # to delete
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict') # required = True à ajouter après migration une fois tous les pays manquants retrouvés
    state_id = fields.Many2one('res.country.state', 'State', ondelete='restrict')
    other_names = fields.Text(string='Other Names',help=u"A list of other ways to write the name of this city, separated by carriage returns")
    latitude = fields.Float(string='Latitude',digit=(7,2))
    longitude = fields.Float(string='Longitude',digit=(7,2))

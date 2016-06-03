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

class create_embassy_folder(models.TransientModel):
    _name = 'create.embassy.folder'
    
    site_id = fields.Many2one('cci_missions.site',string='Site',required=True)
    
    @api.multi
    def create_embassy_folder(self):
        obj_dossier = self.env[self.env.context.get('active_model')]
        data_dossier = obj_dossier.browse(self.env.context.get('active_ids'))
        list_folders = []
        folder_create = 0
        folder_reject = 0
        folder_rej_reason = ""
        for data in data_dossier:
            if data.embassy_folder_id:
                folder_reject = folder_reject + 1
                folder_rej_reason += "ID "+str(data.id)+": Already Has an Embassy Folder Linked. \n"
                continue
            folder_create = folder_create + 1
            folder_id = self.env['cci_missions.embassy_folder'].create({
                        'site_id': self.site_id.id,
                        'partner_id': data.order_partner_id.id,
                        'destination_id': data.destination_id.id,
                })
    
            list_folders.append(folder_id.id)
            data.write({'embassy_folder_id' : folder_id.id})
        
        res={}
        res['folder_created'] = str(folder_create)
        res['folder_rejected'] = str(folder_reject)
        res['folder_rej_reason'] = str(folder_rej_reason)
        res['folder_ids'] = list_folders
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'open.embassy.folder',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': res,
        }
    
class open_embassy_folder(models.TransientModel):
    
    _name = 'open.embassy.folder'
    
    folder_created = fields.Char(string='Embassy Folder Created',readonly=True)
    folder_rejected = fields.Char(string='Embassy Folder Rejected',readonly=True)
    folder_rej_reason = fields.Text(string='Error Messages',readonly=True)
    folder_ids = fields.Many2many('cci_missions.embassy_folder','wizard_create_embessay_folder_rel','emb_wizard_id','folder_id')
    
    @api.model
    def default_get(self, fields):
        res = super(open_embassy_folder, self).default_get(fields)
        res.update({'folder_created': self.env.context.get('folder_created',False),
                    'folder_rejected':self.env.context.get('folder_rejected',False),
                    'folder_rej_reason':self.env.context.get('folder_rej_reason',False),
                    'folder_ids':[(6,0,self.env.context.get('folder_ids',[]))] #self.env.context.get('folder_ids',False)
                    })
        return res
    
    @api.multi
    def open_folder(self):
        mission_datas = self.folder_ids.read(['crm_case_id'])
        mission_datas = mission_datas and str([mission_datas[0]['id']]) or str([])
        val = {
            'domain': "[('id','in', "+mission_datas+")]",
            'name': 'Folder',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'cci_missions.embassy_folder',
            'view_id': False,
            'context' : "{}",
            'type': 'ir.actions.act_window'
            }
        return val

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


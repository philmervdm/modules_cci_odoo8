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
# Version 1.1 2011-07-25 Philmer export in two excel files rather than seding a mail with a csv file
from openerp import models, fields, api , _
from openerp import tools
from openerp.exceptions import Warning

import time
import datetime
import base64
from xlwt import *

def past_month():
    past_month = str(int(time.strftime('%m'))-1)
    if past_month == '0':
        past_month = '12'
    return past_month

def year_past_month():
    past_month_year = int(time.strftime('%Y'))
    if int(time.strftime('%m')) == 1:
        past_month_year = past_month_year - 1
    return past_month_year

MONTHS = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December')
]

msg_fields = {
    'new_atas':{'string': 'New Atas of this month',
        'type': 'binary',
        'readonly': True,},
    'finished_atas':{'string': 'Finished Atas of this month',
        'type': 'binary',
        'readonly': True,},
}

def lengthmonth(year, month):
    if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
        return 29
    return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]


class wizard_fed_send(models.TransientModel):
    _name = 'wizard.fed.send'
    
    month = fields.Selection(selection=MONTHS,string ='Month',required=True ,default = past_month())
    year = fields.Integer(string = 'Year', size = 4,required= True,default = year_past_month())


    @api.multi
    def get_files(self):
        # first, create the file with new atas of this month
        # Determine the first and last date to select
        month = self.month
        year = int(self.year)
        date_begin = datetime.date(year,int(month),1).strftime('%Y-%m-%d')
        date_end = datetime.date(year,int(month),lengthmonth(year, int(month))).strftime('%Y-%m-%d')
        
        obj_carnet = self.env['cci_missions.ata_carnet']
        carnets = obj_carnet.search([('creation_date','>=',date_begin),('creation_date','<=',date_end)])
#         if carnet_ids:
#             carnets = obj_carnet.browse(cr,uid,carnet_ids)
#         else:
#             carnets = []

        wb1 = Workbook()
        ws1 = wb1.add_sheet('New ATA Carnets')
        ws1.write(0,0,'Euler_ID')
        ws1.write(0,1,'Name')
        ws1.write(0,2,'VAT_Num')
        ws1.write(0,3,'CarnetNum')
        ws1.write(0,4,'Value')
        ws1.write(0,5,'Emission')
        ws1.write(0,6,'CCI')
        ws1.write(0,7,'CPD')
        ws1.write(0,8,'Remarques')
        line = 1
        for carnet in carnets:
            remarks = ''
            if carnet.own_risk and carnet.warranty > 0.0:
                remarks = 'Caution:'+str(carnet.warranty)
            cpd = ( 'CPD' in carnet.type_id.name ) and 1 or 0
            if carnet.partner_id.insurer_id:
                euler_id = str(carnet.partner_id.insurer_id).rjust(10,'0')
            else:
                euler_id = ''
            ws1.write(line,0,euler_id)
            ws1.write(line,1,carnet.partner_id.name or '')
            ws1.write(line,2,carnet.partner_id.vat or '')
            ws1.write(line,3,'BE/'+carnet.name)
            ws1.write(line,4,carnet.goods_value or 0.0)
            ws1.write(line,5,carnet.creation_date[8:10]+'-'+carnet.creation_date[5:7]+'-'+carnet.creation_date[0:4])
            ws1.write(line,6,'cci connect')
            ws1.write(line,7,cpd)
            ws1.write(line,8,remarks)
            line += 1
        wb1.save('new_atas.xls')
        if carnets:
            carnets.write({'federation_sending_date' : time.strftime('%Y-%m-%d')})
        result_file = open('new_atas.xls','rb').read()

        # second, create the file with atas finished this month
        # Determine the first and last date to select
        month = self.month
        year = int(self.year)
        date_begin = datetime.date(year-2,int(month),1).strftime('%Y-%m-%d')
        date_end = datetime.date(year-2,int(month),lengthmonth(year, int(month))).strftime('%Y-%m-%d')
        
        obj_carnet = self.env['cci_missions.ata_carnet']
        carnet_ids1 = obj_carnet.search([('state','=','correct'),('return_date','>=',date_begin),('return_date','<=',date_end)])
        carnet_ids2 = obj_carnet.search([('state','in',['closed','pending']),('creation_date','>=',date_begin),('creation_date','<=',date_end)])
        carnets = carnet_ids1 + carnet_ids2
#         if carnet_ids:
#             carnets = obj_carnet.browse(cr,uid,carnet_ids)

        wb2 = Workbook()
        ws2 = wb2.add_sheet('Finished ATA Carnets')
        ws2.write(0,0,'Euler_ID')
        ws2.write(0,1,'Name')
        ws2.write(0,2,'VAT_Num')
        ws2.write(0,3,'CarnetNum')
        ws2.write(0,4,'Value')
        ws2.write(0,5,'Emission')
        ws2.write(0,6,'CCI')
        ws2.write(0,7,'CPD')
        ws2.write(0,8,'Remarques')
        if carnets:
            line = 1
            for carnet in carnets:
                remarks = ''
                if carnet.own_risk and carnet.warranty > 0.0:
                    remarks = 'Caution:'+str(carnet.warranty)
                cpd = ( 'CPD' in carnet.type_id.name ) and 1 or 0
                if carnet.partner_id.insurer_id:
                    euler_id = str(carnet.partner_id.insurer_id).rjust(10,'0')
                else:
                    euler_id = ''
                ws2.write(line,0,euler_id)
                ws2.write(line,1,carnet.partner_id.name or '')
                ws2.write(line,2,carnet.partner_id.vat or '')
                ws2.write(line,3,'BE/'+carnet.name)
                ws2.write(line,4,carnet.goods_value or 0.0)
                ws2.write(line,5,carnet.creation_date[8:10]+'-'+carnet.creation_date[5:7]+'-'+carnet.creation_date[0:4])
                ws2.write(line,6,'cci connect')
                ws2.write(line,7,cpd)
                ws2.write(line,8,remarks)
                line += 1
        else:
            ws2.write(1,0,'0000000000')
            ws2.write(1,1,'[None]')
            ws2.write(1,2,'')
            ws2.write(1,3,'[None]')
            ws2.write(1,4,0.0)
            ws2.write(1,5,'')
            ws2.write(1,6,'cci connect')
            ws2.write(1,7,0)
            ws2.write(1,8,'')
        wb2.save('finished_atas.xls')
        result_file2 = open('finished_atas.xls','rb').read()
        # give the result tos the user
        msg = 'Save the Files with '".xls"' extension.'
        new_atas = base64.encodestring(result_file)
        finished_atas = base64.encodestring(result_file2)
        ctx = self.env.context.copy()
        ctx.update({'msg':msg,'new_atas':new_atas,'finished_atas':finished_atas})
        
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.fed.send.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

class wizard_fed_send_msg(models.TransientModel):
    _name = 'wizard.fed.send.msg'

    msg = fields.Text(string = 'File created',readonly = True)
    name = fields.Char(string='Name')
    name2 = fields.Char(string='Name')
    new_atas = fields.Binary(string = 'New Atas of this month',readonly = True)
    finished_atas = fields.Binary(string = 'Finished Atas of this month',readonly = True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_fed_send_msg, self).default_get(fields)
        res['msg'] = self.env.context.get('msg','')
        res['name'] = 'new_atas.xls'
        res['name2'] = 'finished_atas.xls'
        res['new_atas'] = self.env.context.get('new_atas',False)
        res['finished_atas'] = self.env.context.get('finished_atas',False)
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



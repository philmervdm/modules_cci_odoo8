# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2013-TODAY OpenERP S.A. (<http://openerp.com>).
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

from openerp.tests import common


class Test_Base_Contact(common.TransactionCase):

    def setUp(self):
        """*****setUp*****"""
        super(Test_Base_Contact, self).setUp()
        cr, uid = self.cr, self.uid
        ModelData = self.registry('ir.model.data')
        self.partner = self.registry('res.partner')
        self.act_window = self.registry('ir.actions.act_window')

        # Get test records reference
        for attr, module, name in [
                ('main_partner_id', 'base', 'main_partner'),
                ('bob_contact_id', 'base_contact', 'res_partner_contact1'),
                ('bob_job1_id', 'base_contact', 'res_partner_contact1_work_position1'),
                ('roger_contact_id', 'base', 'res_partner_main2'),
                ('roger_job2_id', 'base_contact', 'res_partner_main2_position_consultant')]:
            r = ModelData.get_object_reference(cr, uid, module, name)
            setattr(self, attr, r[1] if r else False)

    def test_00_show_only_standalone_contact(self):
        """Check that only standalone contact are shown if context explicitly state to not display all positions"""
        cr, uid = self.cr, self.uid
        ctx = {'search_show_all_positions': False}
        partner_ids = self.partner.search(cr, uid, [], context=ctx)
        partner_ids.sort()
        self.assertTrue(self.bob_job1_id not in partner_ids)
        self.assertTrue(self.roger_job2_id not in partner_ids)

    def test_01_show_all_positions(self):
        """Check that all contact are show if context is empty or explicitly state to display all positions"""
        cr, uid = self.cr, self.uid

        partner_ids = self.partner.search(cr, uid, [], context=None)
        self.assertTrue(self.bob_job1_id in partner_ids)
        self.assertTrue(self.roger_job2_id in partner_ids)

        ctx = {'search_show_all_positions': True}
        partner_ids = self.partner.search(cr, uid, [], context=ctx)
        self.assertTrue(self.bob_job1_id in partner_ids)
        self.assertTrue(self.roger_job2_id in partner_ids)

    def test_02_reading_other_contact_one2many_show_all_positions(self):
        """Check that readonly partner's ``other_contact_ids`` return all values whatever the context"""
        cr, uid = self.cr, self.uid

        def read_other_contacts(pid, context=None):
            return self.partner.read(cr, uid, [pid], ['other_contact_ids'], context=context)[0]['other_contact_ids']

        def read_contacts(pid, context=None):
            return self.partner.read(cr, uid, [pid], ['child_ids'], context=context)[0]['child_ids']

        ctx = None
        self.assertEqual(read_other_contacts(self.bob_contact_id, context=ctx), [self.bob_job1_id])
        ctx = {'search_show_all_positions': False}
        self.assertEqual(read_other_contacts(self.bob_contact_id, context=ctx), [self.bob_job1_id])
        ctx = {'search_show_all_positions': True}
        self.assertEqual(read_other_contacts(self.bob_contact_id, context=ctx), [self.bob_job1_id])

        ctx = None
        self.assertTrue(self.bob_job1_id in read_contacts(self.main_partner_id, context=ctx))
        ctx = {'search_show_all_positions': False}
        self.assertTrue(self.bob_job1_id in read_contacts(self.main_partner_id, context=ctx))
        ctx = {'search_show_all_positions': True}
        self.assertTrue(self.bob_job1_id in read_contacts(self.main_partner_id, context=ctx))

    def test_03_search_match_attached_contacts(self):
        """Check that searching partner also return partners having attached contacts matching search criteria"""
        cr, uid = self.cr, self.uid
        # Bob's contact has one other position which is related to 'Your Company'
        # so search for all contacts working for 'Your Company' should contain bob position.
        partner_ids = self.partner.search(cr, uid, [('parent_id', 'ilike', 'YourCompany')], context=None)
        self.assertTrue(self.bob_job1_id in partner_ids)

        # but when searching without 'all positions', we should get the position standalone contact instead.
        ctx = {'search_show_all_positions': False}
        partner_ids = self.partner.search(cr, uid, [('parent_id', 'ilike', 'YourCompany')], context=ctx)
        self.assertTrue(self.bob_contact_id in partner_ids)

    def test_04_contact_creation(self):
        """Check that we're begin to create a contact"""
        cr, uid = self.cr, self.uid

        # Create a contact using only name
        new_contact_id = self.partner.create(cr, uid, {'name': 'Bob Egnops'})
        self.assertEqual(self.partner.browse(cr, uid, new_contact_id).contact_type, 'standalone')

        # Create a contact with only contact_id
        new_contact_id = self.partner.create(cr, uid, {'contact_id': self.bob_contact_id})
        new_contact = self.partner.browse(cr, uid, new_contact_id)
        self.assertEqual(new_contact.name, 'Bob Egnops')
        self.assertEqual(new_contact.contact_type, 'attached')

        # Create a contact with both contact_id and name;
        # contact's name should override provided value in that case
        new_contact_id = self.partner.create(cr, uid, {'contact_id': self.bob_contact_id, 'name': 'Rob Egnops'})
        self.assertEqual(self.partner.browse(cr, uid, new_contact_id).name, 'Bob Egnops')

        # Reset contact to standalone
        self.partner.write(cr, uid, [new_contact_id], {'contact_id': False})
        self.assertEqual(self.partner.browse(cr, uid, new_contact_id).contact_type, 'standalone')

    def test_05_contact_fields_sync(self):
        """Check that contact's fields are correctly synced between parent contact or related contacts"""
        cr, uid = self.cr, self.uid

        # Test DOWNSTREAM sync
        self.partner.write(cr, uid, [self.bob_contact_id], {'name': 'Rob Egnops'})
        self.assertEqual(self.partner.browse(cr, uid, self.bob_job1_id).name, 'Rob Egnops')

        # Test UPSTREAM sync
        self.partner.write(cr, uid, [self.bob_job1_id], {'name': 'Bob Egnops'})
        self.assertEqual(self.partner.browse(cr, uid, self.bob_contact_id).name, 'Bob Egnops')

        # Test existing standalone contact assignation to an existing contact
        # - create a new person, then assign it to an existing contact.
        new_contact_id = self.partner.create(cr, uid, {'name': 'UnitTest Contact'})
        self.assertEqual(self.partner.browse(cr, uid, new_contact_id).name, 'UnitTest Contact')
        self.partner.write(cr, uid, [new_contact_id], {'contact_id': self.bob_contact_id})
        self.assertEqual(self.partner.browse(cr, uid, new_contact_id).name, 'Bob Egnops')

        # Test that when write both contact and contact's sync field, value of contact prevail
        self.partner.write(cr, uid, [self.bob_job1_id], {'contact_id': self.roger_contact_id, 'name': 'Bob Egnops'})
        self.assertEqual(self.partner.browse(cr, uid, self.bob_job1_id).name, 'Roger Scott',
            'When updating both contact and name fields, contact name should prevail')

        # Test corner case for `update_contact`. Calling it without context and
        # without an update on a contact's synced field. Normally this should
        # not happen, as it's already being enforced by check in `_fields_sync`.
        self.partner.update_contact(cr, uid, [self.bob_contact_id], {'function': 'Actor'})
        self.assertEqual(self.partner.browse(cr, uid, self.bob_contact_id).function, False)
        self.assertEqual(self.partner.browse(cr, uid, self.bob_contact_id).name, 'Bob Egnops')

        # Test corner cases for `_contact_sync_from_parent`. Calling it on a
        # partner having no contact, i.e no sync should be performed on it.
        # Normally this should not happen, as it's already being enforced by
        # check in `_fields_sync`.
        new_contact_id2 = self.partner.create(cr, uid, {'name': 'UnitTest Contact2'})
        new_contact2 = self.partner.browse(cr, uid, new_contact_id2)
        self.partner._contact_sync_from_parent(cr, uid, new_contact2)
        self.assertEqual(self.partner.browse(cr, uid, new_contact_id2).name, 'UnitTest Contact2')

    def test_06_contact_unlink(self):
        """Check that when unlinking a standalone contact, attached contact are not deleted"""
        cr, uid = self.cr, self.uid

        # Unlink Bob contact
        self.partner.unlink(cr, uid, [self.bob_contact_id])

        # Check that Bob has been deleted, but Bob @ YourCompany still exist
        self.assertFalse(self.partner.exists(cr, uid, [self.bob_contact_id]))
        self.assertTrue(self.partner.exists(cr, uid, [self.bob_job1_id]))

    def test_07_u_onchange_contact_id(self):
        """Check that on change "contact" work as expected"""
        cr, uid = self.cr, self.uid

        # no contact provided, means no 'name' in return
        rval = self.partner.onchange_contact_id(cr, uid, [], False)
        self.assertTrue('name' not in (rval.get('value') or {}))

        # contact provided, ensure we return the contact's name
        rval = self.partner.onchange_contact_id(cr, uid, [], self.bob_contact_id)
        self.assertEqual((rval.get('value') or {}).get('name'), 'Bob Egnops')

    def test_08_u_onchange_contact_type(self):
        """Check that on change "contact type" work as expected"""
        cr, uid = self.cr, self.uid

        # For standalone contact, force empty contact_id
        rval = self.partner.onchange_contact_type(cr, uid, [], 'standalone')
        self.assertTrue('contact_id' in rval['value'] and rval['value']['contact_id'] is False)

        # For attached contact, should not update contact
        rval = self.partner.onchange_contact_type(cr, uid, [], 'attached')
        self.assertTrue('contact_id' not in rval['value'])

    def test_09_actwindow_default_allpositions_context(self):
        """Check that the 'search_show_all_positions' are automatically added
           on all ir.act.window where is not explicitly specified"""
        cr, uid = self.cr, self.uid

        action_contacts_id = self.ref('contacts.action_contacts')
        action_partner_title_id = self.ref('base.action_partner_title_partner')

        # When model is res.partner and we request action context, check that
        # 'search_show_all_positions' is corretly added
        action = self.act_window.read(cr, uid, action_contacts_id, ['context'])
        self.assertTrue('search_show_all_positions' in action['context'],
            'reading context of single act_window on model res.partner should add search_show_all_positions in context')

        # variant for multiple ids
        action = self.act_window.read(cr, uid, [action_contacts_id], ['context'])
        self.assertTrue('search_show_all_positions' in action[0]['context'],
            'reading context of multiple act_window on model res.partner should add search_show_all_positions in context')

        # variant when requesting for context and other fields
        action = self.act_window.read(cr, uid, [action_contacts_id], ['context', 'name', 'res_model'])
        self.assertTrue('search_show_all_positions' in action[0]['context'],
            'reading context and other fields of multiple act_window on model res.partner should add search_show_all_positions in context')

        # check we do no crash when 'not requesting' context
        action = self.act_window.read(cr, uid, action_contacts_id, ['res_model'])
        self.assertEqual(action['res_model'], 'res.partner',
            'reading other fields on single act_window should not alter data')

        # check we do not add 'search_show_all_positions' for action with
        # res_model != 'res.partner'
        action = self.act_window.read(cr, uid, [action_partner_title_id], ['res_model', 'context'])
        self.assertTrue('search_show_all_positions' not in action[0]['context'],
            'reading multiple act_window on model different from res.partner should not add search_show_all_positions in context')

        # corner case, reading action with id 0 should return False
        action = self.act_window.read(cr, uid, 0, ['res_model'])
        self.assertEqual(action, False,
            'when trying to read act_window with id 0, read should return False')

        # check that action with a specified 'search_show_all_positions' in
        # context are not altered
        self.act_window.write(cr, uid, [action_contacts_id], {'context': '{"search_show_all_positions": True}'})
        action = self.act_window.read(cr, uid, action_contacts_id, [])
        self.assertTrue('"search_show_all_positions": True' in action['context'],
            "reading a single act_window context with 'search_show_all_positions' already defined should not be altered")

        self.act_window.write(cr, uid, [action_partner_title_id], {'context': '{"search_show_all_positions": True}'})
        action = self.act_window.read(cr, uid, [action_partner_title_id], [])
        self.assertTrue('"search_show_all_positions": True' in action[0]['context'],
            "reading multiple act_window context with 'search_show_all_positions' already defined should not be altered")

    def test_10_search_showallpositions(self):
        """Check that when searching on res.partner with special context, 'search_show_all_positions' in preserved"""
        cr, uid = self.cr, self.uid

        ctx = {'search_show_all_positions': True}
        self.partner._basecontact_check_context(cr, uid, 'search', context=ctx)
        self.assertTrue('search_show_all_positions' in ctx)
        self.assertEqual(ctx['search_show_all_positions'], True)

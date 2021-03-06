################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################

from plone.app.testing import SITE_OWNER_NAME as portal_owner
from plone.app.testing import TEST_USER_NAME as default_user
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_PASSWORD
from Products.Archetypes.tests.attestcase import ATTestCase
from plone.protect import createToken

from StringIO import StringIO

html = """\
<html>
<head><title>Foo</title></head>
<body>Bar</body>
</html>
"""


class TestFunctionalObjectCreation(ATTestCase):
    """Tests object renaming and creation"""

    def afterSetUp(self):
        # basic data
        self.folder_url = self.folder.absolute_url()
        self.folder_path = '/%s' % self.folder.absolute_url(1)
        self.basic_auth = '%s:%s' % (default_user, TEST_USER_PASSWORD)
        self.owner_auth = '%s:%s' % (portal_owner, SITE_OWNER_PASSWORD)
        # We want 401 responses, not redirects to a login page
        plugins = self.portal.acl_users.plugins
        try:
            from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
            plugins.deactivatePlugin(IChallengePlugin,
                                     'credentials_cookie_auth')
        except (KeyError, ImportError):
            pass

        # disable portal_factory as it's a nuisance here
        if hasattr(self.portal.aq_base, 'portal_factory'):
            self.portal.portal_factory.manage_setPortalFactoryTypes(listOfTypeIds=[])

        # error log
        from Products.SiteErrorLog.SiteErrorLog import temp_logs
        temp_logs.clear()  # clean up log
        self.error_log = self.portal.error_log
        self.error_log._ignored_exceptions = ()

        self.setupCTR()

    def setupCTR(self):
        # Modify the CTR to point to SimpleType
        ctr = self.portal.content_type_registry
        if ctr.getPredicate('text'):
            # ATCT has a predict
            ctr.removePredicate('text')
        ctr.addPredicate('text', 'major_minor')
        ctr.getPredicate('text').edit('text', '')
        ctr.assignTypeName('text', 'DDocument')
        ctr.reorderPredicate('text', 0)
        return ctr

    def assertStatusEqual(self, a, b, msg=''):
        """Helper method that uses the error log to output useful debug infos
        """
        if a != b:
            entries = self.error_log.getLogEntries()
            if entries:
                msg = entries[0]['tb_text']
            else:
                if not msg:
                    msg = 'no error log msg available'
                    self.assertEqual(a, b)
        self.assertEqual(a, b, msg)

    def publish(self, path, basic=None, env=None, extra=None,
                request_method='GET', stdin=None, handle_errors=True):
        """ Override publish method using zope.testbrowser with CSFR protection
        """
        if not extra:
            extra = {}
        extra['_authenticator'] = createToken()
        return ATTestCase.publish(
             self, path, basic, env, extra, request_method, stdin,
             handle_errors)

    def test_id_change_with_non_auto_id(self):
        """Make sure Id is only set when original id is autogenerated"""
        # Make our content type use auto generated ids
        from Products.Archetypes.examples.DDocument import DDocument
        DDocument._at_rename_after_creation = True

        auto_id = 'orig_id'

        # create an object with an autogenerated id
        response = self.publish(self.folder_path +
                                '/invokeFactory?type_name=DDocument&id=%s' % auto_id,
                                self.basic_auth)

        # XXX now lets test if http://plone.org/collector/4487 is present
        if "base_edit.cpt" in self.portal.portal_skins.archetypes.objectIds():
            raise AttributeError, ("test_id_change_with_non_auto_id "
                  "is expected to fail unless  http://plone.org/collector/4487 is fixed")

        self.assertTrue(auto_id in self.folder.objectIds())
        new_obj = getattr(self.folder, auto_id)

        # Change the title
        obj_title = "New Title for Object"
        new_obj_path = '/%s' % new_obj.absolute_url(1)
        self.assertTrue(new_obj.checkCreationFlag())  # object is not yet edited

        # Edit object
        response = self.publish('%s/base_edit?form.submitted=1&title=%s&body=Blank' % (new_obj_path, obj_title,), self.basic_auth)
        self.assertStatusEqual(response.getStatus(), 302)  # OK
        self.assertFalse(new_obj.checkCreationFlag())  # object is fully created
        self.assertEqual(new_obj.Title(), obj_title)  # title is set
        self.assertEqual(new_obj.getId(), auto_id)  # id should not have changed

        del DDocument._at_rename_after_creation

    def test_id_change_with_without_marker(self):
        # Id should not be changed unless _at_rename_after_creation is set
        # on the class.
        # Make our content type use auto generated ids
        from Products.Archetypes.examples.DDocument import DDocument
        try:
            del DDocument._at_rename_after_creation
        except (AttributeError, KeyError):
            pass

        auto_id = 'orig_id'

        # create an object with an autogenerated id
        response = self.publish(self.folder_path +
                                '/invokeFactory?type_name=DDocument&id=%s' % auto_id,
                                self.basic_auth)

        # XXX now lets test if http://plone.org/collector/4487 is present
        if "base_edit.cpt" in self.portal.portal_skins.archetypes.objectIds():
            raise AttributeError("test_id_change_with_without_marker is "
                  "expected to fail unless http://plone.org/collector/4487 is "
                  "fixed. This might also occur with chameleon cache files "
                  "but chameleon not installed. You can find them via: "
                  "find . -name \"*pt.py\"")

        self.assertTrue(auto_id in self.folder.objectIds())
        new_obj = getattr(self.folder, auto_id)

        # Change the title
        obj_title = "New Title for Object"
        new_obj_path = '/%s' % new_obj.absolute_url(1)
        self.assertTrue(new_obj.checkCreationFlag())  # object is not yet edited

        # Edit object
        response = self.publish('%s/base_edit?form.submitted=1&title=%s&body=Blank' % (new_obj_path, obj_title,), self.basic_auth)
        self.assertStatusEqual(response.getStatus(), 302)  # OK
        self.assertFalse(new_obj.checkCreationFlag())  # object is fully created
        self.assertEqual(new_obj.Title(), obj_title)  # title is set
        self.assertEqual(new_obj.getId(), auto_id)  # id should not have changed

    def test_update_schema_does_not_reset_creation_flag(self):
        # This is functional so that we get a full request and set the flag

        # create an object with flag set
        self.publish(self.folder_path +
                     '/invokeFactory?type_name=DDocument&id=new_doc',
                     self.basic_auth)
        self.assertTrue('new_doc' in self.folder.objectIds())
        new_obj = self.folder.new_doc
        self.assertTrue(new_obj.checkCreationFlag())  # object is not yet edited
        obj_title = "New Title for Object"
        # Edit object
        self.publish('/%s/base_edit?form.submitted=1&title=%s&body=Blank' % (
                     new_obj.absolute_url(1), obj_title), self.basic_auth)

        # now lets test if http://plone.org/collector/4487 is present
        if "base_edit.cpt" in self.portal.portal_skins.archetypes.objectIds():
            raise AttributeError, ("test_update_schema_does_not_reset_creation_flag "
                  "is expected to fail unless  http://plone.org/collector/4487 is fixed")

        self.assertFalse(new_obj.checkCreationFlag())  # object is fully created
        # Now run the schema update
        req = self.app.REQUEST
        req.form['update_all'] = True
        req.form['Archetypes.DDocument'] = True
        self.portal.archetype_tool.manage_updateSchema(REQUEST=req)
        self.assertFalse(new_obj.checkCreationFlag())

    def test_createObjectViaWebDAV(self):
        # WebDAV upload should create new document without creation flag set
        response = self.publish(self.folder_path + '/new_html',
                                env={'CONTENT_TYPE': 'text/html'},
                                request_method='PUT',
                                stdin=StringIO(html),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.assertTrue('new_html' in self.folder.objectIds())
        self.assertEqual(self.folder.new_html.portal_type, 'DDocument')
        self.assertEqual(self.folder.new_html.getBody(), html)
        self.assertFalse(self.folder.new_html.checkCreationFlag())

    def test_createObjectInCodeDoesNotSetFlag(self):
        # Using invokeFactory from code should not set the creation flag

        # Functional sets the method to GET, this isn't really a functional
        # test but is a special case for the previous tests, so we'll unset
        # the REQUEST_METHOD.
        self.app.REQUEST.set('REQUEST_METHOD', 'nonsense')

        self.folder.invokeFactory('DDocument', 'bogus_item')
        self.assertTrue('bogus_item' in self.folder.objectIds())
        self.assertFalse(self.folder.bogus_item.checkCreationFlag())

        self.app.REQUEST.set('REQUEST_METHOD', 'GET')

    def test_at_download_checks_read_permission(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('SimpleFile', 'test')
        self.portal.portal_workflow.doActionFor(self.portal.test, 'publish')

        # give it a file field with a restricted read_permission
        schema = self.portal.test.schema = self.portal.test.Schema().copy()
        from Products.Archetypes.Field import FileField
        schema['file'] = FileField('file', read_permission = 'Manage portal')

        res = self.publish('/plone/test/at_download/file')
        self.assertEqual(res.status, 401)

    def test_webdav_btree_folder(self):
        portal = self.layer['portal']
        self.setRoles(['Manager'])
        portal.invokeFactory('SimpleBTreeFolder', 'simple_btree_folder')
        portal.invokeFactory('DDocument', 'index_html', title='Root Index')
        folder = portal.simple_btree_folder
        self.assertNotIn('index_html', folder.objectIds())
        self.assertEqual(str(folder.index_html), "<DDocument at index_html>")
        response = self.publish("/plone/simple_btree_folder/index_html",
                                basic=self.basic_auth,
                                request_method="PUT",
                                stdin=StringIO('Simple BTree Folder Index'))
        self.assertEqual(response.getStatus(), 201)
        self.assertIn('index_html', folder.objectIds())
        self.assertEqual(folder.index_html.title_or_id(), 'index_html')
        self.assertEqual(str(folder.index_html.body()).strip(), 'Simple BTree Folder Index')

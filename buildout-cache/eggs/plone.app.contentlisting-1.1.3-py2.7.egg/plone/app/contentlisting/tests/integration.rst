Basic usage
===========

The idea behind plone.app.contentlisting is to have a unified way of listing
Plone content whenever needed, whether in folderlistings, collections,
portlets or search results.

It should be simple to use for new developers and integrators. The core concept
is to take a list of something (in this case a catalog result set) and turn it
into an IContentListing so that the user always knows what to expect.

    >>> from zope import interface
    >>> from plone.app.contentlisting.interfaces import IContentListing, IContentListingObject
    >>> from Products.CMFCore.utils import getToolByName

We simply adapt a sequence of something content-like. In this case (and most
common cases) the sequence will be a catalog search result set.

    >>> catalog = getToolByName(self.portal, 'portal_catalog')
    >>> results = catalog.searchResults(dict(is_default_page=False))
    >>> contentlist = IContentListing(results)
    >>> print(contentlist)
    <plone.app.contentlisting.contentlisting.ContentListing object ...>

We get a ContentListing. That is the catalog based implementation of
IContentListing. In other cases you might get a different implementations,
but they should all conform to the rules of the interface.

The contentListing is a normal iterator that we can loop over. Each entry is
a CatalogContentListingObject

    >>> listitem = contentlist[2]
    >>> print(listitem)
    <plone.app.contentlisting.catalog.CatalogContentListingObject instance ...>

The listitem provides all the methods of the IContentListingObject interface

    >>> print(listitem.review_state())
    published

It can report what its source of data is

    >>> print(listitem.getDataOrigin())
    <Products.ZCatalog.Catalog.mybrains object at...>

and if we access attributes on it that are not in the interface or in the
brain, it will transparently fetch the real object and cache it to get
properties from that instead.

After accessing an attribute of the object that was neither in the
IContentListingObject or on the catalog brain, we can now see that the
real object has been silently fetched in the background. getDataOrigin now
returns the object.

    >>> dummy= listitem.absolute_url()
    >>> print(listitem.getDataOrigin())
    <Folder at news>

This item's origin is no longer a Brain, but the real object

    >>> listitem.review_state()
    'published'

For user and integrator convenience we also include a couple of handy
browser views to get to these listings.

    >>> folderlisting = self.portal.restrictedTraverse('@@folderListing')()
    >>> print(folderlisting)
    <plone.app.contentlisting.contentlisting.ContentListing object ...

    >>> len(folderlisting)
    3

We can even slice the new folderlisting

    >>> len (folderlisting[2:4])
    1

    >>> len(self.portal.restrictedTraverse('news/@@folderListing')())
    1

And we can use batching in it:

    >>> [i.getURL() for i in self.portal.restrictedTraverse('@@folderListing')()]
    ['http://nohost/plone/test-folder', 'http://nohost/plone/front-page', 'http://nohost/plone/news']
    >>> [i.getURL() for i in self.portal.restrictedTraverse('@@folderListing')(batch=True, b_size=1)]
    ['http://nohost/plone/test-folder']
    >>> [i.getURL() for i in self.portal.restrictedTraverse('@@folderListing')(batch=True, b_start=1, b_size=1)]
    ['http://nohost/plone/front-page']
    >>> [i.getURL() for i in self.portal.restrictedTraverse('@@folderListing')(batch=True, b_start=2, b_size=1)]
    ['http://nohost/plone/news']
    >>> [i.getURL() for i in self.portal.restrictedTraverse('@@folderListing')(batch=True, b_start=1, b_size=2)]
    ['http://nohost/plone/front-page', 'http://nohost/plone/news']

We can use filtering by catalog indexes:
    >>> len(self.portal.restrictedTraverse('@@folderListing')(portal_type='Document'))
    1


Append View Action
==================

Some types may require '/view' appended to their URLs. Currently these don't

    >>> frontpage = self.portal.restrictedTraverse('@@folderListing')(id='front-page')[0]
    >>> frontpage.appendViewAction()
    ''
    >>> news = self.portal.restrictedTraverse('@@folderListing')(id='news')[0]
    >>> news.appendViewAction()
    ''
    >>> realfrontpage = IContentListingObject(self.portal['front-page'])
    >>> realfrontpage.appendViewAction()
    ''

By altering portal_properties, we can make this true for Documents

    >>> ttool = getToolByName(self.portal, 'portal_properties')
    >>> ttool.site_properties.typesUseViewActionInListings = [frontpage.portal_type]
    >>> frontpage.appendViewAction()
    '/view'
    >>> news.appendViewAction()
    ''
    >>> realfrontpage.appendViewAction()
    '/view'

And turn it off again

    >>> ttool.site_properties.typesUseViewActionInListings = []
    >>> frontpage.appendViewAction()
    ''
    >>> news.appendViewAction()
    ''
    >>> realfrontpage.appendViewAction()
    ''


Visibility in Navigation
========================

Items by default are visible in navigation

    >>> frontpage = self.portal.restrictedTraverse('@@folderListing')(id='front-page')[0]
    >>> frontpage.isVisibleInNav()
    True

    >>> news = self.portal.restrictedTraverse('@@folderListing')(id='news')[0]
    >>> news.isVisibleInNav()
    True

Just to check, these will be catalog objects using a brain internally

    >>> frontpage.__class__
    <class 'plone.app.contentlisting.catalog.CatalogContentListingObject'>
    >>> print(frontpage.getDataOrigin())
    <Products.ZCatalog.Catalog.mybrains object at...>
    >>> frontpage.isVisibleInNav()
    True

A catalog object with a real object works

    >>> dummy= listitem.absolute_url()
    >>> print(listitem.getDataOrigin())
    <Folder at news>
    >>> frontpage.isVisibleInNav()
    True

Getting a realobject-based listing also works

    >>> realfrontpage = IContentListingObject(self.portal['front-page'])
    >>> realfrontpage.__class__
    <class 'plone.app.contentlisting.realobject.RealContentListingObject'>
    >>> realfrontpage.isVisibleInNav()
    True

There are several ways something can be hidden from navigation, the most direct
way is the exclude_from_nav property being true

    >>> frontpage_object = frontpage.getObject()
    >>> frontpage_object.exclude_from_nav = True
    >>> frontpage_object.reindexObject()

This will be indexed, so an object isn't necessary to check this

    >>> frontpage = self.portal.restrictedTraverse('@@folderListing')(id='front-page')[0]
    >>> frontpage.isVisibleInNav()
    False
    >>> print(frontpage.getDataOrigin())
    <Products.ZCatalog.Catalog.mybrains object at...>

But a real object still works.

    >>> realfrontpage = IContentListingObject(self.portal['front-page'])
    >>> realfrontpage.__class__
    <class 'plone.app.contentlisting.realobject.RealContentListingObject'>
    >>> realfrontpage.isVisibleInNav()
    False

We can also turn it off again.

    >>> frontpage_object.exclude_from_nav = False
    >>> frontpage_object.reindexObject()

    >>> frontpage = self.portal.restrictedTraverse('@@folderListing')(id='front-page')[0]
    >>> frontpage.isVisibleInNav()
    True

    >>> realfrontpage = IContentListingObject(self.portal['front-page'])
    >>> realfrontpage.isVisibleInNav()
    True

We can also exclude anything of a particular type using the displayed type setting::

    >>> from plone.registry.interfaces import IRegistry
    >>> from zope.component import getUtility
    >>> registry = getUtility(IRegistry)
    >>> from Products.CMFPlone.interfaces import INavigationSchema
    >>> navigation_settings = registry.forInterface(
    ...     INavigationSchema,
    ...     prefix='plone'
    ... )
    >>> navigation_settings.displayed_types = (frontpage.portal_type, news.portal_type)
    >>> frontpage.isVisibleInNav()
    True
    >>> realfrontpage.isVisibleInNav()
    True
    >>> news.isVisibleInNav()
    True
    >>> navigation_settings.displayed_types = ()
    >>> frontpage.isVisibleInNav()
    False
    >>> realfrontpage.isVisibleInNav()
    False
    >>> news.isVisibleInNav()
    False

Finally, particular ids can be excluded from listings

    >>> navigation_settings.displayed_types = (frontpage.portal_type, news.portal_type)
    >>> navtree_properties = getattr(getToolByName(self.portal, 'portal_properties'), 'navtree_properties')
    >>> navtree_properties.idsNotToList = [news.id]
    >>> frontpage.isVisibleInNav()
    True
    >>> realfrontpage.isVisibleInNav()
    True
    >>> news.isVisibleInNav()
    False
    >>> navtree_properties.idsNotToList = []
    >>> frontpage.isVisibleInNav()
    True
    >>> realfrontpage.isVisibleInNav()
    True
    >>> news.isVisibleInNav()
    True

from zope.interface import implements
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.portlet.static import PloneMessageFactory as _

# Import the base portlet module whose properties we will modify
from plone.app.portlets.portlets import news

class IMyNewsPortlet(news.INewsPortlet):
    """ Defines a new portlet "my news portlet" which takes properties of the existing static text portlet. """
    pass

class MyNewsPortletRenderer(news.Renderer):
    """ Overrides static.pt in the rendering of the portlet. """
    render = ViewPageTemplateFile('mynews_portlet.pt')

class MyNewsPortletAssignment(news.Assignment):
    """ Assigner for my news portlet. """
    implements(IMyNewsPortlet)

class MyNewsPortletAdd(news.AddForm):
    """ Make sure that add form creates instances of our custom portlet instead of the base class portlet. """
    def create(self, data):
        return MyNewsPortletAssignment(**data)
        
        
  
# stdlib
from inspect import isclass

# 3rd-party modules
from lxml import etree

class RunstatTable(object):
  """
  DOCUMENT-ME
  """
  ITER_XPATH = None
  NAME_XPATH = 'name'
  VIEW = None

  ### -------------------------------------------------------------------------
  ### CONSTRUCTOR
  ### -------------------------------------------------------------------------

  def __init__(self, ncdev, table_xml = None):
    self._ncdev = ncdev
    self._xml_got = table_xml
    self.view = self.VIEW

  ### -------------------------------------------------------------------------
  ### PROPERTIES
  ### -------------------------------------------------------------------------

  @property
  def N(self):
    """ shortcut to the Netconf instance """
    return self._ncdev

  @property
  def R(self):
    """ shortcut to the Netconf RPC metaexec instance """
    return self._ncdev.rpc

  @property
  def xml(self):
    """ 
    returns the XML data received from the device.  for tables within
    tables, this XML will be the parent XML element that contains the
    table contents.
    """
    return self._xml_got

  @property
  def got(self):
    """ returns the XML data recieved from the device """
    return self.xml

  @property
  def view(self):
    """ returns the current view assigned to this table """
    return self._view

  @view.setter
  def view(self, cls):
    """ :cls: must either be a RunstatView or None """

    if cls is None:
      self._view = None
      return

    if not isclass(cls):
      raise ValueError("Must be given RunstatView class")

    self._view = cls

  @property
  def _iter_xpath(self):
    """ internal use only """
    return self.got.xpath(self.ITER_XPATH) if self.got is not None else []
  
  ### -------------------------------------------------------------------------
  ### METHODS
  ### -------------------------------------------------------------------------

  def assert_data(self):
    """ ensure that the table has XML data """
    if self._xml_got is None: raise RuntimeError("No data")

  def get(self, **kvargs):
    """ 
    executes the 'get' command to load the XML data from the 
    Netconf instance.  If you need to create a 'stub' for unit-testing
    purposes, you want to create a subclass of your table and overload 
    this methods.
    """
    args = {}
    args.update(self.GET_ARGS)
    args.update(kvargs)
    self._xml_got = getattr(self.R,self.GET_RPC)(**args)

    # returning self for call-chaining purposes, yo!
    return self

  def keys(self):
    """ returns a list of table item names """
    if self.ITER_XPATH is None: return []
    return [n.findtext(self.NAME_XPATH).strip() for n in self._iter_xpath]

  def values(self):
    """ 
    returns list of table entry items().  
    """
    if self.view is None:
      # no View, so provide XML for each item
      return [this for this in self]
    else:
      # view object for each item
      return [this.items() for this in self]

  def items(self):
    """ returns list of tuple(name,values) for each table entry """
    return zip(self.keys(), self.values())

  ### -------------------------------------------------------------------------
  ### OVERLOADS
  ### -------------------------------------------------------------------------

  def __repr__(self):
    cname = self.__class__.__name__
    if self.ITER_XPATH is not None:
      return "%s\n@%s: %s items" % (cname, self.N.hostname, len(self))
    else:
      return "%s\n@%s: data=%s" % (cname, self.N.hostname, ('no','yes')[self.got is not None])

  # ---------------------------------------------------------------------------
  # len is the number of items in the table
  # ---------------------------------------------------------------------------

  def __len__(self):
    return 1 if not self.ITER_XPATH else len(self._iter_xpath)

  # ---------------------------------------------------------------------------
  # [<name>]: select a table item based on <name>
  # [0]: gives the only view, for composite table
  # ---------------------------------------------------------------------------

  def __getitem__(self,value):
    """
    returns a table item.  if a table view is set (should be by default) then
    the item will be converted to the view upon return.  if there is no table 
    view, then the XML object will be returned.

    :value:
      when it is a string, this will perform a select based on the name
      when it is a number, this will perform a select based by position.
        nubers can be either positive or negative.
        [0] is the first item (first xpath is actually 1)
        [-1] is the last item
    """
    self.assert_data()

    if self.ITER_XPATH is None:
      # this is a table of tables; i.e. not table of record views
      found = self.got
    else:
      if isinstance(value,str):
        # find by name
        xpath = self.ITER_XPATH + '[normalize-space(%s)="' % self.NAME_XPATH + value + '"]'
      elif isinstance(value,int):
        # find by index, assuming caller is using 0-index, and might use
        # negative values to reference from end of list
        xpath_pos = value + 1
        if value < 0:
          xpath_pos = len(self) + xpath_pos
        xpath = '%s[%s]' % (self.ITER_XPATH, xpath_pos)

      found = self.got.xpath(xpath)
      if not len(found): return None
      found = found[0]

    return self.view(table=self, view_xml=found) if self.view is not None else found

  # ---------------------------------------------------------------------------
  # iterate though each item in the talbe, not applicable for composite table
  # ---------------------------------------------------------------------------

  def __iter__(self):
    """ iteratable of each toplevel xpath item """
    self.assert_data()
    itself = lambda x: x
    view = lambda x: self.view(self, x)

    item_as = view if self.view else itself

    for this in self.got.xpath(self.ITER_XPATH):
      yield item_as(this)

import pdb
from pprint import pprint as pp
from lxml.builder import E
from lxml import etree

# junos "ez" module
from jnpr.eznc import Netconf

dev = Netconf(host='jnpr-dc-fw',user='jeremy')
dev.open()

## now play around with dev object ...
## when done, you should issue dev.close()


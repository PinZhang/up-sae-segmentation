import sae
import web
from handlers import *

app = web.application(urls, globals()).wsgifunc()
application = sae.create_wsgi_app(app)


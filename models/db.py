# -*- coding: utf-8 -*-

import datetime

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    #db = DAL(myconf.get('db.uri'), 
    #         pool_size = myconf.get('db.pool_size'),
    #         migrate_enabled = myconf.get('db.migrate'),
    #         check_reserved = ['all'])
    db = DAL('postgres://sms:vmo123@127.0.0.1:5432/sms')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''


## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Service, PluginManager

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'))
service = Service()
plugins = PluginManager()

## create all tables needed by auth if not custom tables
#auth.define_tables(username=False, signature=False)
db.define_table("tarifas",
    Field("nombre", length=56, notnull=True,default=None, label="Nombre Tarifa", writable=True), format='%(nombre)s',migrate=True)

auth.settings.extra_fields['auth_user']= [
    Field('nombres', length=128, default=''),
    Field('rut', length=28, default=''),
    Field('direccion', length=128, default=''),
    Field('email', length=128, default='', unique=True), # required
    Field('password', 'password', length=512,            # required
        readable=False, label='Password'),
    Field('giro',length=128, default=''),
    Field('prepago','boolean', default='t',notnull=True),
    Field("saldo", "integer", notnull=True, label='Fallidos',default=0,writable=False),
    Field("tarifa", db.tarifas, notnull=True, label='Tarifa',writable=True),
    Field('telefono',length=128, default=''),
    Field('registration_key', length=512,                # required
        writable=False, readable=False, default=''),
    Field('reset_password_key', length=512,              # required
        writable=False, readable=False, default=''),
    Field('registration_id', length=512,                 # required
        writable=False, readable=False, default='')]

db.auth_user.tarifa.requires = IS_IN_DB(db,db.tarifas.id,'%(nombre)s')

auth.define_tables(username=False, signature=False)

##configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
db.define_table("gateway",
    Field("nombre", "string", length=56, notnull=True, label="Gateway Nombre", writable=True),
    Field("url", "string", length=256, notnull=True, label="URL", writable=True),
    Field("estado", "boolean", notnull=True, label="Estado Gateway", default='t', writable=True), format='%(nombre)s',migrate=True)

db.define_table("estadosms",
    Field("nombre","string", length=56,notnull=True,default=None, label="Estado SMS",writable=True),format='%(nombre)s',migrate=True)

db.define_table("lista",
    Field("nombre","string", length=56,notnull=True,default=None, label="Nombre Lista",writable=True),
    Field("id_clte",db.auth_user, notnull=True,writable=False),format='%(nombre)s',migrate=True)

db.define_table("contactos",
    Field("numero","string", length=56, notnull=True, default=None, label="Numero", writable=True),
    Field("msg","string", length=140, notnull=True, default='', label="Texto Mensaje", writable=True),
    Field("gw",db.gateway, notnull=False, label="Gateway",writable=False),
    Field("id_lista",db.lista, notnull=True, label="Lista",writable=False),
    Field("envio","datetime", notnull=False, label="Envio",writable=False),
    Field("entrega","datetime", notnull=False, label="Entrega",writable=False),
    Field("estado",db.estadosms, notnull=True,default=1,writable=False),migrate=True)

db.contactos.id_lista.requires = IS_IN_DB(db,db.lista.id,'%(nombre)s')
db.contactos.estado.requires = IS_IN_DB(db,db.estadosms.id,'%(nombre)s')

db.define_table("campain",
   Field("nombre", "string", length=56, notnull=True, default=None, label='Nombre',writable=True),
   Field("fecha", "datetime", notnull=True,label='Fecha Inicio',default=datetime.datetime.now(),writable=True),
#   Field("Total", "integer", notnull=True, label='Total',default=0,writable=False),
#   Field("Pendientes", "integer", notnull=True, label='Pendientes',default=0,writable=False),
#   Field("Cola", "integer", notnull=True, label='Enviados',default=0,writable=False),
#   Field("Enviados", "integer", notnull=True, label='Enviados',default=0,writable=False),
#   Field("Entregados", "integer", notnull=True, label='Entregados',default=0,writable=False),
#   Field("Fallidos", "integer", notnull=True, label='Fallidos',default=0,writable=False),
   Field("id_clte", db.auth_user, notnull=True,writable=False),
   Field("id_lista", db.lista, notnull=True,writable=True),
   Field("estado", "boolean", notnull=True, label='Estado', default='t',writable=True),format='%(nombre)s',migrate=True)

db.campain.id_lista.requires = IS_IN_DB(db,db.lista.id,'%(nombre)s')
db.campain.id_clte.requires = IS_IN_DB(db,db.auth_user.id,'%(nombres)s')

db.define_table("tarifas",
    Field("nombre", length=56, notnull=True,default=None, label="Nombre Tarifa", writable=True), format='%(nombre)s',migrate=True)

db.define_table("prefix",
    Field("prefix", "string", length=56, notnull=True, label="Prefijo", writable=True),
    Field("tarifa", db.tarifas, notnull=True, label="Nombre Tarifa", writable=True),
    Field("estado", "boolean", notnull=True, default='t', label="Estado", writable=True),
    Field("nombre", "string", length=56, notnull=True, label="Nombre Prefijo", writable=True),  format='%(nombre)s',migrate=True)

db.prefix.tarifa.requires = IS_IN_DB(db,db.tarifas.id,'%(nombre)s')





auth.settings.actions_disabled.append('register') 

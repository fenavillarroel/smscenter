# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    #response.flash = T("Hello World")
    return dict(message=T('Welcome to web2py!'))


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

@auth.requires_login()
def lista():
   
    r=request.args
    if r:
        l=db.executesql('select * from lista where id=%s' % r[0])[0]
        i=l[0]
        n=l[1]
    else:
        i,n='',''


    #if form.accepts(request.vars,session):
    if request.vars:

        try:
            db.executesql("update lista set nombre='%s' where id=%s" % (request.vars.nombre,request.vars.id))
            db.commit()
        except:
            pass
        redirect(URL('rlistas'))

    return dict(i=i,n=n)

@auth.requires_login()
def addcampain():

    l=db.executesql('select nombre,id from lista where id_clte=%s order by nombre asc' % auth.user.id)
    d={}
    for i in l:
        d[i[1]]=i[0]

    form=SQLFORM.factory(Field('nombre','string',length=56,requires=IS_NOT_EMPTY()),
                        Field('fecha','datetime',requires=IS_DATETIME(format='%Y-%m-%d %H:%M:%S'),default=datetime.datetime.now()),
                        Field('lista','integer',requires=IS_IN_SET(d),represent= lambda value, row: d[value]),
                        Field('estado','boolean',default='f'),formstyle='bootstrap',_class="form-group")

    if form.process().accepted:

        clte = db.executesql('select prepago,saldo from auth_user where id=%s' % (auth.user.id,))[0]

        if clte[0]:

            if clte[1] <= 0: #Sin saldo prepago no puede crear campañas
        
                session.flash = T("Su cuenta no registra Saldo Para Crear Campaña!!!")
                redirect(URL("campain"))

            

        if form.vars.estado:
            e='T'
        else:
            e='F'
        try:
            db.executesql("insert into campain (nombre,fecha,id_clte,id_lista,estado) values ( \
                            '%s','%s',%s,%s,'%s')" % (form.vars.nombre,form.vars.fecha,auth.user.id,form.vars.lista,e))
            db.commit()
        except:
            session.flash = T("Error al Crear Campaña!!!")
            redirect(URL("campain"))
            
        session.flash = T("Campaña Correctamente Creada!!!")

        redirect(URL('campain'))

    return dict(form=form)
    
@auth.requires_login()
def addlist():

    if request.vars:

        clte = db.executesql('select prepago,saldo from auth_user where id=%s' % (auth.user.id,))[0]
    

        if clte[0]: #Saber si es prepago

            if clte[1] <= 0: #Sin saldo prepago no puede crear Listas
        
                session.flash = T("Su cuenta no registra Saldo Para Crear Listas !!!")
                redirect(URL("rlistas"))

        db.executesql("insert into lista (nombre,id_clte) values ('%s',%s)" % (request.vars.nombre,auth.user.id))
        db.commit()
        l=db.executesql("select currval('lista_id_seq')")[0][0]
        session.flash = T("Lista Correctamente Creada!!!")

        redirect(URL('uploadfile',args=[auth.user.id,l]))

    return locals()

@auth.requires_login()
def rlistas():

    rws=db.executesql('select * from lista where id_clte=%s order by id desc' % (auth.user.id,))

    return dict(rws=rws)


@auth.requires_login()
def campain():

    rws  =  db.executesql('select id,nombre,fecha,estado,  \
                                (select count(*) as total from contactos  \
                                join lista on contactos.id_lista=lista.id    \
                                where campain.id_clte=%s and campain.id_lista=lista.id),   \
                                (select count(*) as pendiente from contactos \
                                join lista on contactos.id_lista=lista.id \
                                join estadosms on estadosms.id=contactos.estado  \
                                where campain.id_clte=%s and campain.id_lista=lista.id and estadosms.id=1), \
                                (select count(*) as cola from contactos \
                                join lista on contactos.id_lista=lista.id \
                                join estadosms on estadosms.id=contactos.estado  \
                                where campain.id_clte=%s and campain.id_lista=lista.id and estadosms.id=2), \
                                (select count(*) as enviados from contactos \
                                join lista on contactos.id_lista=lista.id \
                                join estadosms on estadosms.id=contactos.estado  \
                                where campain.id_clte=%s and campain.id_lista=lista.id and  estadosms.id=3), \
                                (select count(*) as entregados from contactos \
                                join lista on contactos.id_lista=lista.id \
                                join estadosms on estadosms.id=contactos.estado  \
                                where campain.id_clte=%s and campain.id_lista=lista.id and estadosms.id=4), \
                                (select count(*) as fallidos from contactos \
                                join lista on contactos.id_lista=lista.id \
                                join estadosms on estadosms.id=contactos.estado  \
                                where campain.id_clte=%s and campain.id_lista=lista.id and estadosms.id=5) \
                            from campain    \
                            where id_clte=%s    \
                            order by id desc' % (auth.user.id,auth.user.id,auth.user.id,auth.user.id,auth.user.id,auth.user.id,auth.user.id))

    return dict(rws=rws)


@auth.requires_login()
def updatecampain():

    c=request.args[0]

    l=db.executesql('select nombre,id from lista where id_clte=%s order by nombre asc' % auth.user.id)
    d={}
    for i in l:
        d[i[1]]=i[0]
    dat=db.executesql('select * from campain where id=%s' % (c,))[0]
    cam=dat[4]
    if dat[5]=='T' or dat[5]=='t':
        v=True
    else:
        v=False

    form=SQLFORM.factory(Field('nombre','string',length=56,requires=IS_NOT_EMPTY(),default=dat[1]),
                        Field('fecha','datetime',requires=IS_DATETIME(format='%Y-%m-%d %H:%M:%S'),default=dat[2]),
                        Field('lista','integer',requires=IS_IN_SET(d),default=cam),
                        Field('estado','boolean',default=v),formstyle='bootstrap',_class="form-group")



    if form.process().accepted:

        if form.vars.estado:
            e='T'
        else:
            e='F'
        try:

            db.executesql("update campain set nombre='%s', fecha='%s',id_lista=%s,estado='%s' where id=%s" % (form.vars.nombre,form.vars.fecha,form.vars.lista,e,c))
            db.commit()
        except:

            session.flash = T("Error al Actuaizar Campaña!!!")
            redirect(URL('campain'))

        session.flash = T("Campaña Actuaizada!!!")
        redirect(URL('campain'))


    return dict(form=form)

@auth.requires_login()
def contactos():

    idlista=request.args[0]

    rws=db.executesql('select contactos.id,contactos.numero,contactos.msg,estadosms.nombre from contactos \
                        join estadosms on estadosms.id=contactos.estado \
                        where contactos.id_lista=%s \
                        order by contactos.id desc' % (idlista,))


    return dict(rws=rws)

@auth.requires_login()
def uploadfile():

    id_user,lista=request.args[0],request.args[1]

    form=SQLFORM.factory(Field('Archivo','upload',custom_store=store_file),formstyle='bootstrap',_class="form-group")
    #form.process(formname='form')
    form1=SQLFORM.factory(Field('Mensaje','text',requires=IS_NOT_EMPTY()),
                        Field('Archivo','upload',custom_store=store_file),formstyle='bootstrap',_class="form-group")
    #form1.process(formname='form1')

    if form.accepts(request.vars, session,formname='form'):

            with open('applications/smscenter/uploads/'+form.vars.Archivo,'rb') as fin: 
            # csv.DictReader uses first line in file for column headings by default
                dr = csv.reader(fin) # comma is default delimiter
                for row in dr:
                    try:
                        db.executesql("insert into contactos (numero,msg,id_lista) values ('%s','%s',%s)" % (row[0],row[1],lista))
                        db.commit()
                    except:
                        session.flash = T("Error al Procesar Atchivo CSV Favor Importar Nuevamente!!!")
                        redirect(URL('rlistas'))

            
            os.system('rm %s'% 'applications/smscenter/uploads/'+form.vars.Archivo)
            session.flash = T("Contactos Insertados Correctamente!!!")

            redirect(URL('rlistas'))



    if form1.accepts(request.vars, session,formname='form1'):

            with open('applications/smscenter/uploads/'+form1.vars.Archivo,'rb') as fin: 
            # csv.DictReader uses first line in file for column headings by default
                dr = csv.reader(fin) # comma is default delimiter
                for row in dr:
                    try:
                        db.executesql("insert into contactos (numero,msg,id_lista) values ('%s','%s',%s)" % (row[0],form1.vars.Mensaje,lista))
                        db.commit()
                    except:
                        session.flash = T("Error al Procesar Atchivo CSV Favor Importar Nuevamente!!!")
                        redirect(URL('rlistas'))
            os.system('rm %s'% 'applications/smscenter/uploads/'+form1.vars.Archivo)
            session.flash = T("Contactos y Mensaje Manual Correctamente Insertados!!!")

            redirect(URL('rlistas'))
        

    return dict(form=form,form1=form1)

def store_file(file,filename=None,path=None):
    import os
    import shutil
    path="applications/smscenter/uploads/"
    #if not os.path.exists(path):
    #    os.makedirs(path)
    pathfilename = os.path.join(path, filename)
    dest_file = open(pathfilename, 'wb')
    try:
        shutil.copyfileobj(file, dest_file)
    finally:
        dest_file.close()
    return filename

def retrieve_file(filename, path=None):
    path = "uploads/"
    return (filename, open(os.path.join(path, filename), 'rb'))


@request.restful()
def failedandsent():

    response.view = 'generic.json'

    def POST(*args, **vars):

        idsms=request.vars.idsms
        tipo=request.vars.tipo
        fecha=request.vars.fecha
        entrega=True

        if tipo=='SENT':
            t=3 #Enviado
        elif tipo=='FAILED':
            t=5 #Fallido

        try:
            db.executesql("update contactos set estado='%s', envio=%s where id=%s" % (t,fecha,idsms))
            db.commit()
        except:
            return dict(entrega=False)

        #Descontar saldo del cliente para el SMS Enviado

        if tipo=='SENT':

            #Obtenemos el Id del cliente
            rws=db.executesql("select auth_user.id,contactos.numero from auth_user \
                                    join lista on auth_user.id=lista.id_clte \
                                    join contactos on contactos.id_lista=lista.id \
                                where contactos.id=%s" % (idsms,))[0]

            #Obtenemos el Valor del SMS de la tabla Prefix

            v=db.executesql("select tarifa from prefix where prefix @> '%s' and estado='t'" % (rws[1],))[0]


            #Descontamos el saldo del cliente
            try:

                db.executesql("update auth_user set auth_user.saldo = auth_user.saldo - %s where auth_user.id = %s" % (v[0],rws[0]))
                db.commit()
            except:

                return dict(entrega=False)
            
        return dict(entrega=entrega)

    return locals()

@request.restful()
def delivery():

    response.view = 'generic.json'

    def POST(*args, **vars):

        idsms=request.vars.idsms
        fecha=request.vars.fecha
        entrega=True


        try:
            db.executesql("update contactos set estado=%s, set entrega='%s' where id=%s" % (4,fecha,idsms))
            db.commit()
        except:
            return dict(entrega=False)

        return dict(entrega=entrega)

    return locals()


#!/usr/bin/env python

#standard python libs
import logging
import time
import psycopg2
import json
import requests
import datetime

#third party libs
from daemon import runner

class db:

    def __init__(self,logger):

        self.database='sms'
        self.host='127.0.0.1'
        self.user='sms'
        self.passw='vmo123'
        self.logger=logger
 
    def conectar(self):

        try:
            self.cnx = psycopg2.connect(host=self.host,database=self.database, user=self.user, password=self.passw)
            self.cur=self.cnx.cursor()
            return 1
        except PgSQL.Error, msg:
            self.logger.error("Error: No hay coneccion con la Base de Datos ")
            return 0

    def cerrar(self):

        try:

            self.cur.close()
            self.cnx.close()
            return 1

        except PgSQL.Error, msg:
            self.logger.error("Error: No hay coneccion con la Base de Datos ")
            return 0

    def gateways(self):

        try:
            c=self.conectar()
            if not c:
                self.logger.error("Error: No hay coneccion con la Base de Datos ")
                return None
            else:
                gtw=self.cur.execute("select url from gateway where estado='T' order by random() limit 1")
                res=self.cur.fetchone()
                self.cerrar()
                return res
        except:
                self.logger.error("Error: No hay coneccion con la Base de Datos ")
                return None

    def cola(self,idsms):
        try:
            c=self.conectar()
            if not c:
                self.logger.error("Error: No hay coneccion con la Base de Datos ")
                return None
            else:
                self.cur.execute("update contactos set estado=2 where id=%s" % (idsms,))
                self.cnx.commit()
                self.cerrar()
                return 1
        except:
            self.logger.error("Error: No hay coneccion con la Base de Datos ")
            return None

    def sms(self):

        try:

            c=self.conectar()

            if not c:
                self.logger.error("Error: No hay coneccion con la Base de Datos ")
                return None
            else:
                self.cur.execute("select contactos.id,contactos.numero,contactos.msg from contactos    \
                                    join lista on lista.id=contactos.id_lista   \
                                    join campain on campain.id=lista.id \
                                    where campain.estado='T' and campain.fecha >= '%s' and contactos.estado=1 \
                                    order by random() limit 1" % (datetime.datetime.now(),))

                res=self.cur.fetchone()
                self.cerrar()
                return res

        except:
            
                self.logger.error("Error: No hay coneccion con la Base de Datos ")
                return None


class App():
    
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/var/run/smscenter/smscenter.pid'
        self.pidfile_timeout = 5
                            
    def run(self):

        bbdd=db(logger)
        while True:

            #El codigo principal va aca
            gts=bbdd.gateways()
            if not gts:

                logger.info("No hay Gateways disponibles para el Envio de SMS")

            else:

                dsms=bbdd.sms()

                if dsms:


                    logger.info("Procesando sms Id % Al numero %s por el Gateway %" % (dsms[0],dsms[1],gts[0]))
                    payload={}
                    payload['number']=dsms[1]
                    payload['text']=dsms[2]
                    payload['username']='fenavillarroel'
                    payload['password']='abc123jU'
                    payload['id']=dsms[0]
                    url=gts[0]+'/appsms/default/api'
                    headers={'content-type': 'application/json'}
                    response = requests.post(url, data=json.dumps(payload), headers=headers)
                    if response.ok:
                        bbdd.cola(dsms[0])
                        logger.info("SMS Id % Al numero %s por el Gateway % Enviado Correctamente Su estado esta en COLA" % (dsms[0],dsms[1],gts[0]))

                        #print "OK" #Se actualiza a estado cola
                    else:
                        logger.info("Id SMS %s Gateway %s Responde %s" % (dsms[0],gts[0],response))

                        #print response #Sigue como Pendiente

                else:

                    logger.info("No hay SMS Por Enviar....")


            #Main code goes here ...
            #Note that logger level needs to be set to logging.DEBUG before this shows up in the logs
            #logger.info("Info message Valor de i %s" % (i,))
            #logger.debug("Debug message")
            #logger.info("Info message")
            #logger.warn("Warning message")
            #logger.error("Error message")
            time.sleep(2)

app = App()

logger=logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/smscenter/smscenter.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
#This ensures that the logger file handle does not get closed during daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()

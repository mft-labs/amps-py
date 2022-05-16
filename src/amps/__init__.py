from pydoc import doc
from erlport.erlang import cast, call
from erlport.erlterms import Atom
import json
import uuid
import os
import traceback


class Util:
    def get_id():
        return uuid.UUID(str(uuid.uuid4())).hex


class Logger:
    def __init__(self, sid="", service=None):
        self.sid = sid
        self.service = service

    def log(self, level, message):
        if self.service:
            self.service.__log__(Atom(
                bytes(level, "utf-8")), message)
        else:
            call(Atom(b'Elixir.Amps.PyProcess'), Atom(b'log'), [Atom(
                bytes(level, "utf-8")), message, [(Atom(b'sid'), self.sid)]])

    def info(self, message):
        self.log("info", message)

    def debug(self, message):
        self.log("debug", message)

    def warning(self, message):
        self.log("warning", message)

    def error(self, message):
        self.log("error", message)


class Action:
    def __init__(self, msgdata):
        msgdata = json.loads(msgdata)
        self.msg = msgdata["msg"]
        self.parms = msgdata["parms"]
        self.sysparms = msgdata["sysparms"]
        if self.parms["use_provider"]:
            self.provider = self.parms["provider"]
        if self.msg.get("sid"):
            self.logger = Logger(sid=self.msg["sid"])
        else:
            self.logger = Logger()

    def __run__(self):
        try:
            response = self.action()
        except Exception as e:
            response = {"status": "failed", "reason": traceback.format_exc()}
        return json.dumps(response)

    def send_status(status, reason=""):
        return {"status": "completed", "reason": reason}

    def send_file(status, fpath, meta={}):
        fname = os.path.basename(fpath)
        fsize = os.path.getsize(fpath)
        msg = {**{"fname": fname, "fsize": fsize, "fpath": fpath}, **meta}
        return {"status": status, "msg": msg}

    def send_data(status, data, meta={}):
        msg = {**{"data": data}, **meta}
        return {"status": status, "msg": msg}

    def send_status(status, reason=None):
        if reason:
            return {"status": status, "reason": reason}
        else:
            return {"status": status}

    def action(self):
        return {"status": "completed"}

    def handle_error(self, reason):
        print({"status": "failed", "reason": reason})
        return {"status": "failed", "reason": reason}


class Endpoint(Action):
    def send_resp_data(data, code):
        return {"status": "completed", "response": {"data": data, "code": code}}

    def send_resp_file(fpath, code):
        return {"status": "completed", "response": {"fpath": fpath, "code": code}}


class Service:
    def __init__(self, parms, pid, env, handler, lhandler):
        self.parms = json.loads(parms)
        self.pid = pid
        self.env = env
        self.sid = ""
        self.handler = handler
        self.lhandler = lhandler
        self.logger = Logger(service=self)
        self.initialize()

    def __receive__(self, data):
        try:
            msg = json.loads(data)
            logger = Logger(sid=msg["sid"])

            self.sid = msg.get("sid")
            logger.info(
                f'Message received by Custom Service {self.parms["name"]}')
            resp = self.handle_message(msg, logger)
            self.sid = ""
            return (Atom(b'ok'), resp)
        except Exception as e:
            return (Atom(b'error'), str(e))

    def __send__(self, msg):
        cast(self.pid, msg)

    def __log__(self, level, msg):
        cast(self.lhandler, (Atom(b'log'), (level, msg)))

    def initialize(self):
        pass

    def send_message(self, msg, newmsg):
        msgid = Util.get_id()
        newmsg['parent'] = msg['msgid']
        newmsg['msgid'] = msgid
        if "data" in newmsg:
            del msg["fpath"]
            newmsg["fsize"] = len(newmsg["data"])
        else:
            del msg["data"]
            newmsg["fsize"] = os.path.getsize(newmsg["fpath"])
        call(Atom(b'Elixir.Amps.PyProcess'), Atom(b'send_message'),
             [json.dumps({**msg, **newmsg}), json.dumps(self.parms)])
        return msgid

    def send_new(self, newmsg):
        msgid = Util.get_id()
        newmsg['msgid'] = msgid
        if "data" in newmsg:
            newmsg["fsize"] = len(newmsg["data"])
        else:
            newmsg["fsize"] = os.path.getsize(newmsg["fpath"])
        print(newmsg)
        print(call)
        cast(self.handler, (Atom(b'new'), json.dumps(newmsg)))
        # call(Atom(b'Elixir.Amps.PyProcess'), Atom(b'new_message'),
        #      [json.dumps(newmsg), json.dumps(self.parms), self.env])
        return msgid

    def handle_message(self, data):
        return "completed"

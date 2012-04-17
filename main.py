#!/usr/bin/env python
#-*- coding:utf-8 -*-

import webapp2
from google.appengine.api import channel

import jinja2
import os
import json

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):
    def get(self):
        vars = {}
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(vars))

wait_q = list()
session = dict()

class StatPage(webapp2.RequestHandler):
    def get(self):
        skeys = session.keys()
        skeys = skeys[:len(skeys)/2]
        svals = [session[k] for k in skeys]
        self.response.out.write("""
        <p>Waiting Q: %s</p>
        <p>Sessions: %s</p>""" %(wait_q, zip(skeys, svals)))

class CmdHandler(webapp2.RequestHandler):
    def post(self):
        cmd = self.request.get('cmd')
        if cmd is None:
            self.response.out.write(json.dumps({'error': 'cmd is null'}))
            return
        hdlr = getattr(self, cmd)
        if not hdlr or not callable(hdlr):
            self.response.out.write(json.dumps({'error': 'cannot handle: %s' % cmd}))
            return
        hdlr()

    def connect(self):
        clientid = self.request.get('id')
        if clientid is None:
            self.response.out.write(json.dumps({}))
            return;
        token = channel.create_channel(clientid)
        self.response.out.write(json.dumps({'token':token}))

    def post_message(self):
        msg = self.request.get('msg')
        clientid = self.request.get('id')
        if None in [clientid, msg]:
            return;
        channel.send_message(clientid, json.dumps({'msg':msg}))

    def join_chat(self):
        clientid = self.request.get('id')
        try:
            another = wait_q.pop()
        except IndexError:
            wait_q.append(clientid)
            return
        session[clientid] = another
        session[another] = clientid
        channel.send_message(another, json.dumps({'cmd':'chat_ready'}))
        channel.send_message(clientid, json.dumps({'cmd':'chat_ready'}))

    def leave_chat(self):
        clientid = self.request.get('id')
        if clientid in wait_q:
            wait_q.remove(clientid)
            channel.send_message(clientid, json.dumps({'cmd':'chat_close'}))
            return
        if clientid not in session:
            self.response.out.write(json.dumps({'error':'client not in chat'}))
            return 
        another = session[clientid]
        channel.send_message(another, json.dumps({'cmd':'chat_close'}))
        channel.send_message(clientid, json.dumps({'cmd':'chat_close'}))
        session.pop(clientid)
        session.pop(another)

    def chat_message(self):
        msg = self.request.get('msg')
        clientid = self.request.get('id')
        if clientid not in session:
            self.response.out.write(json.dumps({'error':'client not in chat'}))
            return 
        another = session[clientid]
        channel.send_message(another, json.dumps({'cmd':'chat_message', 'msg':msg}))

app = webapp2.WSGIApplication(
        [('/', MainPage), ('/cmd', CmdHandler), ('/stat', StatPage)],
        debug=True)

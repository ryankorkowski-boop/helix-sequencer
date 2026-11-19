"""Small opt-in phone-link dialog for the existing Tk desktop launcher."""
import threading
import tkinter as tk
from tkinter import ttk
from tools.desktop_remote import RemoteJobs, RemoteServer


def open_phone_link(parent, root):
    previous=getattr(parent,'_phone_link_window',None)
    if previous is not None and previous.winfo_exists():previous.lift();return
    window=tk.Toplevel(parent);parent._phone_link_window=window;window.title('Helix phone remote');window.geometry('660x370')
    panel=ttk.Frame(window,padding=18);panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Control desktop Helix from the Android app',font=('',15)).pack(anchor='w')
    ttk.Label(panel,text='Start this link, then enter this desktop address and pairing key on your phone.\nUse a reachable local network, USB tether, or VPN. No cloud account is needed.').pack(anchor='w',pady=10)
    lan=tk.BooleanVar(value=True);ttk.Checkbutton(panel,text='Allow paired devices on the local network',variable=lan).pack(anchor='w')
    row=ttk.Frame(panel);row.pack(fill='x',pady=6);ttk.Label(row,text='Port').pack(side='left');port=tk.StringVar(value='8765');ttk.Entry(row,textvariable=port,width=8).pack(side='left',padx=8)
    address=tk.StringVar(value='Desktop address: not started');ttk.Label(panel,textvariable=address).pack(anchor='w',pady=6)
    key=tk.StringVar();entry=ttk.Entry(panel,textvariable=key,state='readonly');entry.pack(fill='x')
    state=tk.StringVar(value='Stopped');ttk.Label(panel,textvariable=state,wraplength=600).pack(anchor='w',pady=8)
    link={'server':None}
    def stop():
        server=link['server'];link['server']=None
        if server:threading.Thread(target=server.close,daemon=True).start()
        state.set('Stopped; phone builds cancelled. Completed shows stay in outputs/phone-jobs.')
    def start():
        if link['server']:return
        try:
            number=int(port.get())
            if not 1024<=number<=65535:raise ValueError('Use a port between1024 and65535')
            jobs=RemoteJobs(root/'outputs/phone-jobs');server=RemoteServer(('0.0.0.0' if lan.get() else '127.0.0.1',number),jobs)
            link['server']=server;key.set(jobs.token)
            address.set(('Phone URL: http://<this desktop local IP>:' if lan.get() else 'USB tunnel URL: http://127.0.0.1:')+str(number))
            threading.Thread(target=server.serve_forever,daemon=True).start();state.set('Listening. Keep this dialog and Helix open. A firewall may ask to allow private networks.')
        except Exception as error:state.set('Cannot start phone link: '+str(error))
    def copy():window.clipboard_clear();window.clipboard_append(key.get())
    buttons=ttk.Frame(panel);buttons.pack(fill='x',pady=8)
    for label,action in [('Start link',start),('Copy pairing key',copy),('Stop link',stop)]:ttk.Button(buttons,text=label,command=action).pack(side='left',padx=4)
    def poll():
        server=link['server']
        if server:
            with server.jobs.lock:
                identities=list(server.jobs.jobs)
            if identities:
                item=server.jobs.state(identities[-1]);state.set(item['message']+' · '+item['id'][:8])
        if window.winfo_exists():window.after(1000,poll)
    def destroyed(event):
        if event.widget is window:stop()
    window.bind('<Destroy>',destroyed);window.after(1000,poll)

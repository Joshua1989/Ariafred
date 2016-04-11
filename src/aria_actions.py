# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import xmlrpclib
from workflow import Workflow
from workflow.notify import notify


def set_query(query):
    os_command = 'osascript -e "tell application \\"Alfred 2\\" to search \\"' + query + '\\""'
    os.system(os_command)


def run_aria():
    os_command = 'export PATH=$PATH:/usr/local/bin && aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all -c -D'
    if os.system(os_command) == 0:
        notify('Aria2 has started successfully')
    else:
        notify('Failed to start Aria2, please run manually')


def get_task_name(gid):
    bt = server.tellStatus(gid, ['bittorrent'])
    if bt:
        bt_name = bt['bittorrent']['info']['name']
        file_num = len(server.getFiles(gid))
        name = '{bt_name} (BT: {file_num} files)'.format(bt_name=bt_name, file_num=file_num)
    else:
        path = server.getFiles(gid)[0]['path']
        name = os.path.basename(path)
    return name


def open_dir(gid):
    dir = server.tellStatus(gid, ['dir'])['dir']
    filepath = dir + get_task_name(gid)
    if os.path.exists(filepath):
        os_command = 'open -R "%s"' % filepath
    else:
        os_command = 'open "%s" ' % dir
    os.system(os_command)


def pause_all():
    server.pauseAll()
    notify('All active downloads paused')


def resume_all():
    server.unpauseAll()
    notify('All paused downloads resumed')


def switch_task(gid):
    name = get_task_name(gid)
    status = server.tellStatus(gid, ['status'])['status']
    if status in ['active', 'waiting']:
        server.pause(gid)
        notify('Download paused:', name)
    elif status == 'paused':
        server.unpause(gid)
        notify('Download resumed:', name)
    elif status == 'complete':
        pass
    else:
        urls = server.getFiles(gid)[0]['uris']
        if urls:
            url = urls[0]['uri']
            server.addUri([url])
            server.removeDownloadResult(gid)
            notify('Download resumed:', name)
        else:
            notify('Cannot resume download:', name)


def get_url(gid):
    urls = server.getFiles(gid)[0]['uris']
    if urls:
        url = urls[0]['uri']
        notify('URL has been copied to clipboard:', url)
        print(url, end='')
    else:
        notify('No URL found')


def add_task(url):
    gid = server.addUri([url])
    notify('Download added:', url)


def remove_task(gid):
    name = get_task_name(gid)
    status = server.tellStatus(gid, ['status'])['status']
    if status in ['active', 'waiting', 'paused']:
        server.remove(gid)
    server.removeDownloadResult(gid)
    notify('Download removed:', name)


def clear_stopped():
    server.purgeDownloadResult()
    notify('All stopped downloads cleared')


def quit_aria():
    server.shutdown()
    notify('Aria2 shut down')


def limit_speed(type, speed):
    option = 'max-overall-' + type + '-limit'
    server.changeGlobalOption({option: speed})
    notify('Limit ' + type + ' speed to:', speed + ' KiB/s')

def limit_num(num):
    server.changeGlobalOption({'max-concurrent-downloads': num})
    notify('Limit concurrent downloads to:', num)

def set_rpc(path):
    wf.settings['rpc_path'] = path 
    notify('Set RPC path to: ', path)


def get_help():
    os_command = 'open https://github.com/Wildog/Ariafred'
    os.system(os_command)


def main(wf):
    command = wf.args[0]

    if command == '--open':
        open_dir(wf.args[1])
    elif command == '--rm':
        remove_task(wf.args[1])
    elif command == '--add':
        add_task(wf.args[1])
    elif (command == '--pause' 
        or command == '--resume' 
        or command == '--switch'):
        switch_task(wf.args[1])
    elif command == '--pauseall':
        pause_all()
    elif command == '--resumeall':
        resume_all()
    elif command == '--clear':
        clear_stopped()
    elif command == '--url':
        get_url(wf.args[1])
    elif command == '--rpc-setting':
        set_rpc(wf.args[1])
    elif command == '--run-aria2':
        run_aria()
    elif command == '--quit':
        quit_aria()
    elif command == '--help':
        get_help()
    elif command == '--limit-download':
        limit_speed('download', wf.args[1])
    elif command == '--limit-upload':
        limit_speed('upload', wf.args[1])
    elif command == '--limit-num':
        limit_num(wf.args[1])
    elif command == '--go-rpc-setting':
        set_query('aria rpc ')
    elif command == '--go-active':
        set_query('aria active ')
    elif command == '--go-stopped':
        set_query('aria stopped ')
    elif command == '--go-waiting':
        set_query('aria waiting ')
    elif command == '--go-download-limit-setting':
        set_query('aria limit ')
    elif command == '--go-upload-limit-setting':
        set_query('aria limitup ')


if __name__ == '__main__':

    wf = Workflow()
    rpc_path = wf.settings['rpc_path']
    server = xmlrpclib.ServerProxy(rpc_path).aria2
    sys.exit(wf.run(main))

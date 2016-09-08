# -*- coding: utf-8 -*-
# __author__ = xutao

from __future__ import division, unicode_literals, print_function
# 与 vcenter 交互相关的操作
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
from pyVim.connect import SmartConnect
from pyVmomi import vmodl, vim
import time
import ssl
CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
CONTEXT.verify_mode = ssl.CERT_NONE

HOST = os.getenv("host", "")

PWD = os.getenv("pwd", "")

USERNAME = os.getenv("username", "")


def connect_vcenter(host, username, password, port=443):
    """
        connect to vcenter
    """
    si = SmartConnect(host=host, user=username, pwd=password, port=port, sslContext=CONTEXT)
    return si


def get_obj(content, vimtype, name):
    """
        获取指定 obj
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    container.Destroy()
    return obj


def get_objs(content, vimtype):
    """
        获取 objs
    """
    objs = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    objs = [vm for vm in container.view]
    container.Destroy()
    return objs


def waittask(task, actionName='job', hideResult=False):

    while task.info.state == vim.TaskInfo.State.running or task.info.state == vim.TaskInfo.State.queued:
        print ("task status is %s obj is %s" % (task.info.state, actionName))
        time.sleep(2)

    if task.info.state == vim.TaskInfo.State.success:
        print("task is success")
        if task.info.result is not None and not hideResult:
            return task.info.result
    else:
        if task.info.error is not None:
            raise task.info.error


def change_serialport_config(device):
    """
        edit device config
    """
    dev = vim.vm.device.VirtualDeviceSpec()
    dev.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    dev.device = device
    dev.device.connectable.startConnected = False
    dev.device.connectable.connected = False
    return dev


def filter_problem_vm(vm_obj):
    serialport_count = 0

    serialports = []

    devices = vm_obj.config.hardware.device

    for device in devices:
        if isinstance(device, vim.vm.device.VirtualSerialPort):
            serialport_count += 1
            serialports.append(device)
            print("sesesese count is %s" % serialport_count)
    if serialport_count > 1:
        return True, serialports[1]
    return False, "count is %s" % serialport_count


def reconfig_vm(vm_obj, dev_conf):
    """
        reconfig vm
    """
    vmconf = vim.vm.ConfigSpec()
    vmconf.deviceChange = [dev_conf]
    task = vm_obj.ReconfigVM_Task(spec=vmconf)
    waittask(task=task, actionName="reconfig")


def do_reconfig():
    """
        reconfig task
    """

    si = connect_vcenter(host=HOST, password=PWD, username=USERNAME)

    content = si.content

    vms = get_objs(content, [vim.VirtualMachine])

    print("get all vm .......")
    all_vm = []
    for vm in vms:
        vm_name = vm.name
        print("now vm is %s" % vm_name)

        is_problem_vm, device = filter_problem_vm(vm_obj=vm)

        if is_problem_vm:
            print("vm %s has more than 1 serial port" % vm_name)
            #dev_conf = change_serialport_config(device=device)
            #reconfig_vm(vm_obj=vm, dev_conf=dev_conf)
            all_vm.append(vm_name)
        else:
            print("vm %s is nomal port count is %s" % (vm_name, device))
    return all_vm

if __name__ == "__main__":
    print("start do work....")
    print("*" * 30)
    all_vms = do_reconfig()
    print(len(all_vms))
    for all_vm in all_vms:
        print(all_vm)
    print("end")








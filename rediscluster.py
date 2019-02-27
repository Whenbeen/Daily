#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import argparse
import os
from collections import namedtuple
import logging
import re
import bisect
import time
import subprocess
import redis
import psutil
import paramiko



fileh = logging.FileHandler('rediscluster.log')
consoleh = logging.StreamHandler(sys.stdout)
loghandlers = [fileh, consoleh]

class RedisInstance:
	def __init__( self, ip, port ):
		self.srvip=ip
		self.srvport=port
		self.client=None
		self.state=0    # 0: init  1:master  2:slave
		self.master=None
		return
		
	def __lt__( self, other ):
		if (self.srvip == other.srvip):
			return self.srvport < other.srvport
		else: 
			return self.srvip < other.srvip
			

	def __str__( self ):		
		return	'{}:{}'.format(self.srvip, self.srvport)
		
	def conn( self, pwd ):
		self.client=redis.StrictRedis(host=self.srvip, port=self.srvport, db=0, password=pwd, decode_responses=True)
		# get node id
		nodeinfos=self.client.cluster('nodes')
		logging.debug('redis node %s:%s info - %s', self.srvip, self.srvport, nodeinfos)		
		self.nodeid=list(nodeinfos.values())[0]['node_id']
		logging.info('redis node %s:%s id - %s', self.srvip, self.srvport, self.nodeid)
		return
		
def rediscluster(argv):
	#
	parser = argparse.ArgumentParser(description='Redis Cluster Installer')	
	parser.add_argument('-s', '--hosts', help='redis server host', action='append')
	parser.add_argument('-p', '--password', help='root password', default='storage')		
	parser.add_argument('-v', help='show detail', action='store_true')
		
	args = parser.parse_args();
	if args.v:
		#show detail
		logging.basicConfig(handlers=loghandlers, level=logging.DEBUG)
	else:
		logging.basicConfig(handlers=loghandlers, level=logging.INFO)
	
	logging.info('start create redis cluster...')
	
	if args.hosts:
		# need 6 instance
		sn = len(args.hosts)
		if (sn < 6):
			logging.warn('must have 6 redis instance')
		else:
			srvipmap = {}
			srvarray = []
			for insredis in args.hosts:
				insconf = insredis.split(':')
				redins = RedisInstance(insconf[0], int(insconf[1]))
				bisect.insort(srvarray, redins)
				
			for redobj in srvarray:
				if (redobj.srvip in srvipmap):
					insary=srvipmap[redobj.srvip]
					insary.append(redobj)
				else:
					insary=[redobj]
					srvipmap[redobj.srvip]=insary
							
				
			# cluster
			localips=getAllLocalIPs()
			logging.debug('get local ips %s', localips)
			
			pdir=os.path.dirname(os.path.realpath(__file__))
			logging.debug('package directory is %s', pdir)
			
			# scp installing packages to target host
			for sip,rarray in srvipmap.items():
				logging.info('start install redis in %s', sip)
				if (isLocal(localips, sip)):
					logging.debug('install from local')
					packagedir = os.path.join(pdir, 'packages')
					scpPackages(pdir, sip, targetpath="/home/redispackage/", rootpwd=args.password)
					# install
					installLocal(sip, targetpath="/home/redispackage/", rootpwd=args.password)
				else: 
					logging.debug('install in remote')
					packagedir = os.path.join(pdir, 'packages')
					scpPackages(pdir, sip, targetpath="/home/redispackage/", rootpwd=args.password)					
					# install
					installRemote(sip, targetpath="/home/redispackage/", rootpwd=args.password)
				
				#installRemote(sip, targetpath="/home/redispackage/", rootpwd=args.password)
				# prepare redis
				for robj in rarray:
					prepareredis(sip, robj.srvport, packagepath="/home/redispackage/", rootpwd=args.password)
					
			# cluster it
			setupcluster(srvarray, srvipmap)
			
			logging.info('Redis cluster is up')
	else: 
		logging.warn('please input redis instance list')
		

def getAllLocalIPs():
	local_ips=[]
	ipinfo=psutil.net_if_addrs()
	for k,v in ipinfo.items():
		for item in v:
			if item[0] == 2:
				# add to ip list				
				bisect.insort(local_ips, item[1])
				
	return local_ips


def isLocal( ips, ip ):
	i = bisect.bisect_left(ips, ip)
	if i != len(ips) and ips[i] == ip:
		return True
	return False
	

def scpPackages(root, target, targetpath="/home/redispackage/", rootpwd="storage", port=22):
	# connect target ssh
	ssh = None
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(target,  port=port, username="root", password=rootpwd)
		logging.debug('init target path %s:%s', target, targetpath)
		
		exec_command_remote(ssh, 'rm -fR {}'.format(targetpath))					
		exec_command_remote(ssh, 'mkdir -p {}'.format(targetpath))
				
		sftp = ssh.open_sftp()
		logging.debug('put packages in %s to %s:%s', root, target, targetpath)
		for pfolder, dirs, files in os.walk(root, topdown=True):
			for dname in dirs:
				sdpath=os.path.join(pfolder, dname)
				relpath=os.path.relpath(sdpath, root).replace('\\', '/')
				tdpath='{}{}'.format(targetpath, relpath)
				logging.debug('ftp create directory %s : %s', target, tdpath)
				sftp.mkdir(tdpath)
			for name in files:
				fn, fext = os.path.splitext(name)
				if (fext == '.log'):
					continue
									
				pakpath=os.path.join(pfolder, name)
				relpath = os.path.relpath(pakpath, root).replace('\\', '/')				
				remotepath='{}{}'.format(targetpath, relpath)   # the target must be linux, so do not use os.path.join
				# sftp upload 
				logging.debug('ftp put package %s to %s', pakpath, remotepath)
				sftp.put(pakpath,remotepath)
		
		logging.debug('put packages in %s to %s:%s over', root, target, targetpath)
	finally:
		if ssh:
			ssh.close()		

def scpPackagesLocal(root, target, targetpath="/home/redispackage/", rootpwd="storage", port=22):
	
	try:
		
		logging.debug('init target path %s:%s', target, targetpath)
		
		exec_command_local( 'rm -fR {}'.format(targetpath))					
		exec_command_local( 'mkdir -p {}'.format(targetpath))
				
		logging.debug('put packages in %s to %s:%s', root, target, targetpath)
		for pfolder, dirs, files in os.walk(root, topdown=True):
			for dname in dirs:
				sdpath=os.path.join(pfolder, dname)
				relpath=os.path.relpath(sdpath, root).replace('\\', '/')
				tdpath='{}{}'.format(targetpath, relpath)
				logging.debug('ftp create directory %s : %s', target, tdpath)
				exec_command_local( 'mkdir -p {}'.format(tdpath))
			for name in files:
				fn, fext = os.path.splitext(name)
				if (fext == '.log'):
					continue
									
				pakpath=os.path.join(pfolder, name)
				relpath = os.path.relpath(pakpath, root).replace('\\', '/')				
				remotepath='{}{}'.format(targetpath, relpath)   # the target must be linux, so do not use os.path.join
				# sftp upload 
				logging.debug('local put package %s to %s', pakpath, remotepath)
				exec_command_local( 'cp {0} {1}'.format(pakpath, remotepath))
				
	finally:
		logging.debug('put packages in %s to %s:%s over', root, target, targetpath)
			
def installRemote(target, rootpwd='storage', targetpath="/home/redispackage/", port=22):
	ssh = None
	try:
		finish = 'end of stdOUT buffer. finished with exit status'
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(target,  port=port, username="root", password=rootpwd)
		logging.info('install from path %s:%s', target, targetpath)
		channel = ssh.invoke_shell()
		channel.set_combine_stderr(True)
		stdin = channel.makefile('wb')
		stdout = channel.makefile('r')
		stderr = channel.makefile_stderr('r')
		stdin.write('cd {} \n'.format(targetpath))
		stdin.write('ls -l \n')
		stdin.write('cd {} \n'.format('packages'))
		stdin.write('ls -l \n')
		# rpm -qa jemalloc-3.6.0-1.el7.x86_64.rpm   ; not installed		
		stdin.write('rpm -ivh jemalloc-3.6.0-1.el7.x86_64.rpm \n')
		stdin.write('rpm -ivh redis-4.0.11-1.el7.remi.x86_64.rpm \n')
		echocmd = 'echo {} $? \n'.format(finish)
		stdin.write(echocmd)
		stdin.write('exit')
		stdin.flush()
		
		logging.info('remote info from %s', target)
		for line in stdout:
			logging.info('remote echo: %s', line)
			if str(line).startswith(finish):
				break
		
		#logging.info('remote error from %s', target)	
		#for line in stderr:
		#	logging.info('remote error: %s', line)
		
		logging.info('install in %s:%s is over', target, targetpath)
	finally:
		if ssh:
			ssh.close()		

			
def installLocal(target, rootpwd='storage', targetpath="/home/redispackage/", port=22):
	
	try:		
		cmd01 = ('cd {} '.format(targetpath))
		cmd02 = ('ls -l ')
		cmd03 = ('cd {} '.format('packages'))
		cmd04 = ('ls -l ')		
		cmd05 = ('rpm -ivh jemalloc-3.6.0-1.el7.x86_64.rpm ')
		cmd06 = ('rpm -ivh redis-4.0.11-1.el7.remi.x86_64.rpm ')
		
		installcmds='{0};{1};{2};{3};{4};{5};'.format(cmd01,cmd02,cmd03,cmd04,cmd05,cmd06)
		exec_command_local(installcmds)
		
	finally:
		logging.info('install in %s:%s is over', target, targetpath)
			
			
def prepareredis(target, redisport, packagepath="/home/redispackage/", rootpwd='storage', port=22):
	# prepare conf directory & data directory
	ssh = None
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(target,  port=port, username="root", password=rootpwd)
		logging.info('prepare redis conf %s:%s', target, redisport)
		targetpath='/opt/redis/{}/'.format(redisport)
		exec_command_remote(ssh, 'rm -fR {}'.format(targetpath))
		exec_command_remote(ssh, 'mkdir -p {}'.format(targetpath))
		exec_command_remote(ssh, 'firewall-cmd --add-port={}/tcp --permanent'.format(redisport))
		exec_command_remote(ssh, 'firewall-cmd --reload')
		confdir='{}'.format(targetpath)
		datadir='{}'.format(targetpath)
		#ssh.exec_command('mkdir -p {}'.format(confdir))
		#ssh.exec_command('mkdir -p {}'.format(datadir))
		
		# create redis conf
		conftemp='{}redis.conf'.format(packagepath)
		conffile='{}redis.conf'.format(confdir)
		exec_command_remote(ssh, 'cp {} {}'.format(conftemp, conffile))
		sedcmd='sed -i "s/redisport/{}/g" {}'.format(redisport, conffile)
		exec_command_remote(ssh, sedcmd)
		
		# start redis
		startcmd='redis-server {}'.format(conffile)
		exec_command_remote(ssh, startcmd)   # daemonize yes must in conf file
		time.sleep(5)    # wait for start
	finally:
		if ssh:
			ssh.close()		
			

def exec_command_remote(ssh, cmdstr):
	logging.info('run [%s] on the remote: %s', cmdstr, ssh.get_transport().getpeername())
	stdin, stdout, stderr = ssh.exec_command(cmdstr)
	echoinfo=stdout.read()
	echoerr=stderr.read()
	if (echoinfo):
		logging.info('remote echo: %s', echoinfo)
	if (echoerr):
		logging.info('remote echo: %s', echoerr)
	

def exec_command_local(cmdstr):
	# open sub process
	# cmdstr may have multiple command, each command separated by ';'
	with subprocess.Popen(cmdstr, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) as proc:
		while True:
			line=proc.stdout.readline()
			if line == '' or len(line) == 0:
				break
			else:
				logging.info('remote echo %s', line)
				
	
def connredis( target, redisport, redisobj ):
	# conn redis, get node id
	redisobj.conn('storage')	
	return
	
	
def setupcluster( nodes, ipmap ):
	# match master and slave
	assert len(nodes) % 2 == 0  # just support master-slave mode
	msnum=len(nodes)/2
	masters=[]
	slaves=[]
	
	# conn redis
	for robj in nodes:
		connredis(robj.srvip, robj.srvport, robj)
		
	for ip, objs in ipmap.items():
		if (msnum > 0):
			mobj=objs[0]
			mobj.state=1   # set to master
			masters.append(mobj)
			msnum=msnum - 1
		else:
			break
	
	mi=1		
	while (msnum > 0):		
		for ip, objs in ipmap.items():
			if (msnum > 0 and len(objs)>1):
				mobj=objs[mi]
				mobj.state=1   # set to master
				masters.append(mobj)
				msnum=msnum - 1
			else:
				break
				
		mi=mi+1
				
	for mobj in masters:
		# find slave
		findslave(mobj, ipmap)
					
	# setup cluster
	eversion=1
	for mobj in nodes:
		mobj.client.cluster('SET-CONFIG-EPOCH', eversion)
		eversion=eversion+1
	
	fobj=nodes[0]	
	for x in range(1, len(nodes)):
		tmpobj=nodes[x]
		logging.info('node %s:%s link to %s:%s', fobj.srvip, fobj.srvport, tmpobj.srvip, tmpobj.srvport)
		fobj.client.cluster('meet', tmpobj.srvip, tmpobj.srvport)  # link to cluster
		time.sleep(1)
		
	for mobj in nodes:
		if (mobj.state == 2):
			logging.info('slave %s:%s link master to %s', mobj.srvip, mobj.srvport, mobj.master)
			mobj.client.cluster('replicate', mobj.master)   # link master and slave
			time.sleep(1)
			
	slotnum=int(16384/(len(nodes)/2))
	start=0
	for x in range(0, len(masters)-1):
		mobj=masters[x]
		slots=range(start, start + slotnum)
		logging.info('master %s:%s slots is %s - %s', mobj.srvip, mobj.srvport, start, start + slotnum)
		mobj.client.cluster('addslots', *slots)
		start=start+slotnum
		time.sleep(1)
		
	slots=range(start, 16384)	
	mobj=masters[-1]
	logging.info('master %s:%s slots is %s - %s', mobj.srvip, mobj.srvport, start, 16384)
	mobj.client.cluster('addslots', *slots)
	time.sleep(5)
			
	# hello world
	wi=5
	while (wi > 0):
		clusterinfo=masters[0].client.cluster('info')
		logging.info('cluster info %s', clusterinfo['cluster_state'])
		if (clusterinfo['cluster_state'] == 'ok'):
			logging.info('cluster is ok.')
			break
		wi=wi-1
		time.sleep(2)
		
	return


def findslave( mobj, ipmap ):
	
	for ip, objs in ipmap.items():
		if (mobj.srvip == ip):
			continue
		else:
			for obj in objs:
				if (obj.state == 0 and mobj.srvip < obj.srvip):
					obj.state=2
					obj.master=mobj.nodeid
					logging.info('slave %s:%s attach to master %s:%s', obj.srvip, obj.srvport, mobj.srvip, mobj.srvport)
					return
					
	for ip, objs in ipmap.items():
		if (mobj.srvip == ip):
			continue
		else:
			for obj in objs:
				if (obj.state == 0):
					obj.state=2
					obj.master=mobj.nodeid
					logging.info('slave %s:%s attach to master %s:%s', obj.srvip, obj.srvport, mobj.srvip, mobj.srvport)
					return
					
	objs=ipmap[mobj.srvip]			
	for obj in objs:
		if (obj.state == 0):
			obj.state=2
			obj.master=mobj.nodeid
			logging.info('slave %s:%s attach to master %s:%s', obj.srvip, obj.srvport, mobj.srvip, mobj.srvport)
			break
					
	return
	
	
	
if __name__ == "__main__":
	rediscluster(sys.argv)

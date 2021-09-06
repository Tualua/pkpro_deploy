#!/bin/bash
# RunOnce script for PlayKey Host
# Copyright by Dmitry Popovich, 2021
# dsp@itl24.ru

if [ -e /tmp/runonce ]
then
   rm /tmp/runonce
   sleep 7
   printf "\r\n---- System is being configured! Please do not reset, reboot or power off this computer! ----" > /dev/console
   exec > /root/runonce.log 2>&1
   #  Add gamer SSH key
   chown -R gamer:gamer /home/gamer/
   chmod 700 /home/gamer/.ssh
   chmod 600 /home/gamer/.ssh/authorized_keys
   AQC=$(lspci|grep "AQC"| head -1 | awk '{ print $1 }')
   if [ -z "$AQC" ]
   then
      rpm -ivh /opt/drivers/atlantic-2.4.15.0-1dkms.noarch.rpm
   fi
   printf "\r\n---- Installing RDMA support ----\r\n" > /dev/console
   yum -y install oracle-rdma-release
   yum -y update
   
   printf "\r\n---- Installing ZFS ----\r\n" > /dev/console
   yum -y install http://download.zfsonlinux.org/epel/zfs-release.el7_6.noarch.rpm
   yum -y install zfs
   modprobe zfs
   zpool import data

   printf "\r\n---- Installing GameServer ----\r\n" > /dev/console
   mkdir -p /tmp/update/server
   url=$(/opt/scripts/get_gs.py)
   wget $url -O /tmp/update/server/GameServer.rpm
   yum -y localinstall /tmp/update/server/GameServer.rpm
   systemctl disable gameserver
   PKID=$(cat /tmp/pkid)
   sed -i "s/\$PKID/$PKID/g" /usr/local/etc/gameserver/conf.xml
   
   printf "\r\n---- Configuring network ----\r\n" > /dev/console
   virsh net-destroy default
   virsh net-undefine default
   IFACE=$(cat /tmp/ifname)
   printf "Configuring bridge. System may lose network connectivity\r\n" > /dev/console
   nmcli con delete $IFACE
   nmcli con add type bridge ifname br0
   nmcli con modify bridge-br0 ipv4.method auto
   nmcli con modify bridge-br0 bridge.stp no
   nmcli con add type bridge-slave ifname $IFACE master br0
   CX4=$(lspci|grep "ConnectX-4"| head -1 | awk '{ print $1 }')
   if [ -z "$CX4" ]
   then
      mv /usr/lib/udev/rules.d/99-mlx5-sriov.rules /usr/lib/udev/rules.d/99-mlx5-sriov.disabled
      virsh net-define /opt/etc/default.xml
      virsh net-autostart default
      virsh net-start default
   else
      printf "Found Mellanox ConnectX-4 NIC at PCI $CX4\r\n" > /dev/console
      CX4IFACE=$(ls /sys/bus/pci/devices/0000:$CX4/net/|tail -1|awk '{ print $NF }')
      sed -i "s/\$CX4/$CX4/g" /usr/lib/udev/rules.d/99-mlx5-sriov.rules
      sed -i "s/\$CX4IFACE/$CX4IFACE/g" /opt/etc/passthrough.xml
      printf "Configuring virtual network for SR-IOV\r\n" > /dev/console
      printf "Please do not forget to enable SR-IOV Support in UEFI Settings!\r\n" > /dev/console
      virsh net-define /opt/etc/passthrough.xml
      virsh net-autostart passthrough
      virsh net-start passthrough
   fi
   rm -f /tmp/ifname
   rm -f /tmp/pkid
   printf "\r\n---- Installation complete! Server will be rebooted shortly! ----\r\n" > /dev/console
   systemctl enable gameserver --now
fi

exit

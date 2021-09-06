interface=$(ip addr | grep -i broadcast | awk NR==1'{ print substr($2, 1, length($2)-1)}')
nmcli con delete $interface
nmcli con add type bridge ifname br0
virsh net-define ~/default.xml
virsh net-autostart default
virsh net-start default
nmcli con modify bridge-br0 ipv4.method auto
nmcli con modify bridge-br0 bridge.stp no
nmcli con add type bridge-slave ifname $interface master br0
reboot

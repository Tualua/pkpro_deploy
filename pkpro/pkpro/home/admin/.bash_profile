sed -i '/new-window/d' ~/.tmux.conf
for VM in $(/opt/scripts/listvms.py)
do
   echo "new-window -d -n $VM \"journalctl -fn100 -tgameserver/$VM\"" >> ~/.tmux.conf
done
echo "new-window -d -n voloder \"journalctl -fn100 -u voloder\"" >> ~/.tmux.conf
echo "new-window -d -n CPU \"watch -n1 'cat /proc/cpuinfo|grep MHz'\"" >> ~/.tmux.conf
echo "new-window -d -n Sensors \"watch -n1 sensors\"" >> ~/.tmux.conf
if command -v tmux &> /dev/null && [ -z "$TMUX" ]; then
    tmux attach -t playkey || tmux start; tmux attach -t playkey
fi
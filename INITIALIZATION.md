
# Commands run for screen driver installation

sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
```
sudo bash -c 'cat << EOF > /etc/rc.local
#!/bin/sh -e

exit 0
EOF'
```

sudo chmod +x /etc/rc.local

sudo apt update

// this one takes forever
sudo apt install -y raspi-config

sudo ./LCD35-show

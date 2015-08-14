#! /bin/sh

# oxen client installer
# Copyright (c) 2015 Yoked


if [ "$(id -u)" != "0" ]; then
    cat << EOF >&2
Oxen, because of the actions it performs, requires
root privileges.  Run as root or no oxen.
EOF
    exit 1
fi

if [ "$(uname -s)" != "Linux" ]; then
    echo "Oxen is currently only supported on Linux." >&2
fi

echo "Installing Oxen"


set -e
echo "Creating Oxen Directory (/opt/oxen)"
[ -d /opt/oxen ] && (
    echo "Please remove /opt/oxen before continuing." >&2; exit -1)
mkdir -p /opt/oxen/ || (
    echo "Unable to create directory /opt/oxen." >&2; exit 1)


echo "Creating uninstall script (/opt/oxen/uninstall.sh)"
cat << EOF > /opt/oxen/uninstall.sh
#! /bin/sh +e
systemctl disable yoked-oxen.service 2>/dev/null
rm -f /etc/systemd/system/yoked-oxen.service 2>/dev/null
rm -Rf /opt/oxen/
killall oxen.py
EOF


if [ "x$api_id" != "x" ]; then
    echo "Creating API login config (/opt/oxen/config.ini)"
    echo -n > /opt/oxen/config.ini
    chmod 0600 /opt/oxen/config.ini
    # create configuration file
    cat <<EOF >> /opt/oxen/config.ini
oxen_api_id: $api_id
oxen_api_key: $api_key
EOF
else
    echo "api_id variable not found, skipping config.ini creation."
fi


echo "Creating Oxen (/opt/oxen/oxen.sh)"
cat << "EOF" > /opt/oxen/oxen.sh
#! /bin/bash +e

[ -z "$PYTHON" ] && PYTHON="$(which python)"
output=$(curl -k https://metauser.net/yoked/client/oxen.py | $PYTHON 2>&1)
echo "$output" |tee /var/log/oxen.log

# fix for thundering herd
sleep $(( ( RANDOM % 5 )  + 1 ))

/opt/oxen/oxen.sh &

EOF


echo "Checking Oxen Startup"

cat << EOF > /etc/systemd/system/yoked-oxen.service
[Unit]
Description=Yoked Oxen for managing users SSH Keys on your sytems
After=syslog.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/oxen/
PIDFile=/var/run/oxen.pid
ExecStart=/opt/oxen/oxen.py

[Install]
WantedBy=multi-user.target
EOF

echo "Setting Permissions"
chmod 700 /opt/oxen/ /opt/oxen/uninstall.sh /opt/oxen/oxen.sh

echo "Running oxen.sh"
/opt/oxen/oxen.sh

echo "Launching oxen.py"
set +e;
systemctl enable /etc/systemd/system/oxen.service
systemctl start oxen.service

echo
echo "Finished. Yoked Oxen has been installed."
echo "To remove, run /opt/oxen/uninstall.sh"

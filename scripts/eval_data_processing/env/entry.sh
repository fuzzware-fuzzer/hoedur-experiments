#!/bin/bash

dbus-daemon --nofork &

# create host user
if [ $(id -g user) -ne $USER_GID ]; then
    groupadd -g $USER_GID host
fi
if [ $(id -u user) -ne $USER_UID ]; then
    useradd -s /bin/bash -u ${USER_UID} -g ${USER_GID} host
fi

cmd="sudo -u \#$USER_UID -g \#$USER_GID bash -c \"$*\""
echo $cmd
eval $cmd
require recipes-core/images/isar-image-base.bb

# Common tooling
IMAGE_PREINSTALL += "vim openssh-server"

IMAGE_INSTALL += "customizations sshd-regen-keys"

# Realtime tooling
IMAGE_PREINSTALL += "rt-tests"

# OSADL test image requirements
IMAGE_PREINSTALL += "\
    bc \
    bison \
    flex \
    gcc \
    gpm \
    libelf-dev \
    libncurses5-dev \
    libnet-dns-perl \
    libnuma-dev \
    libssl-dev \
    make \
    munin-node \
    munin-node \
    nasm \
    netpbm \
    ntp \
    rsync \
    rsyslog \
    snmp"

#!/bin/bash
FILENAME_ISO="x86_64-boot-uek.iso"
FILENAME_CKSUM="OracleLinux-R7-U9-Server-x86_64.checksum"
URL_ISO="https://yum.oracle.com/ISOS/OracleLinux/OL7/u9/x86_64/$FILENAME_ISO"
URL_CKSUM="https://linux.oracle.com/security/gpg/checksum/$FILENAME_CKSUM"
CKSUM_ORACLE=$(curl -s $URL_CKSUM|grep "$FILENAME_ISO"|awk '{print $1}')
DIR_OUT="./iso"

function check_iso()
{
    if [[ $1 != $2 ]]
    then
        return 1
    else 
        return 0
    fi
}

function download_iso()
{
    wget $1
}

FLAG_CKSUM=1
while [ $FLAG_CKSUM -ne 0 ]
do
    if [[ -e "$FILENAME_ISO" ]]
    then
        echo "Found $FILENAME_ISO. Checksumming..."
        CKSUM_ISO=$(sha256sum $FILENAME_ISO|awk '{print $1}')
        echo "Downloaded $FILENAME_ISO checksum: $CKSUM_ISO"
        echo "Original $FILENAME_ISO checksum: $CKSUM_ORACLE"
        if [[ $CKSUM_ISO != $CKSUM_ORACLE ]]
        then
            echo "Checksums does not match!"
            rm -f $FILENAME_ISO
        else
            echo "Checksums match!"
            FLAG_CKSUM=0
        fi
    else
        echo "Downloading $FILENAME_ISO"
        download_iso $URL_ISO
    fi
done

isoinfo -f -R -i $FILENAME_ISO | while read line; do
  d=$(dirname $line)
  od=${DIR_OUT}${d}
  [ -f $od ] && rm -f $od
  [ -d $od ] || mkdir -p $od
  isoinfo -R -i $FILENAME_ISO -x $line > ${DIR_OUT}${line}
done
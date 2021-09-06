set -x
SRCPWD=$(pwd)
cd ../pkpro
rm -f ../iso/images/pkpro.img
find . | cpio -c -o | gzip -9cv > ../iso/images/pkpro.img
cd $SRCPWD/iso
genisoimage -U -r -v -T -J -joliet-long -V "PKPROINST" -volset "PKPROINST" -A "PKPROINST" -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e images/efiboot.img -no-emul-boot -o ../PKPROUEK.iso .
implantisomd5 ../PKPROUEK.iso
/bin/cp -rf ../PKPROUEK.iso /vol1/video/downloads/
set +x

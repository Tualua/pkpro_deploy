# Сборщик установочного образа PlayKey Pro

`download_iso.sh` - скачивает загрузочный образ Oracle Linux 7.9 с ядром UEK6

`create_iso.sh` - собирает установочный образ PlayKey Pro

## Инструкция

    git clone https://github.com/Tualua/pkpro_deploy.git
    cd pkpro_deploy
    ./download_iso.sh
    ./create_iso.sh

    Записываем полученный образ при помощи Fedora Media Writer на USB-флэшку

## Особенности

- Должно работать на всех процессорах, включая AMD Ryzen 5000, благодаря использованию в установщике ядра Unbreakable Enterprise Kernel Release 6, основанного на Linux Kernel 5.4
- Используется QEMU версии 4.2, потому обычный образ Windows НЕ БУДЕТ работать, требуется обновление драйверов virtio
- Поддерживается нормальная работа видеокарт AMD Radeon 6000
- Поддержка сетевых карт Aquantia (в процессе тестирования)

## TODO

- [ ] Создание пула ZFS при его отсутствии
- [ ] Тестирование работы сетевых карт Aquantia

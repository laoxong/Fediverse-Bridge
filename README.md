Fediverse-Bridge 项目主要目的是从其他地方自动转发至Misskey

代码参(抄)考(袭):
[cyborg-ubyvtsya/telegram-mastodon-bridge](https://github.com/cyborg-ubyvtsya/telegram-mastodon-bridge)

[ybw2016v/bilibili2notes](https://github.com/ybw2016v/bilibili2notes)

进程守护:
```
cat <<'TEXT' > /etc/systemd/system/fediversebridge.service
[Unit]
Description=TG to misskey daemon
After=network.target

[Install]
WantedBy=multi-user.target

[Service]
Type=simple
WorkingDirectory=/root/Fediverse-Bridge
ExecStart=/usr/bin/python3 -m main.py
Restart=always
TEXT
```
将`WorkingDirectory`修改为程序所在目录,
在通过进程守护运行前请手动运行一次,设置配置文件!
通过 `systemctl start fediversebridge` 启动

`systemctl enable fediversebridge` 设置开机自起

关闭 `systemctl stop fediversebridge`

禁用开机自起: `systemctl disable fediversebridge`

原README.md
<details>
  <summary>cyborg-ubyvtsya/telegram-mastodon-bridge Readme.md</summary>
  # Telebridge

![demonstration](https://github.com/cyborg-ubyvtsya/telegram-mastodon-bridge/blob/main/img/demo.gif)

Telegram/Mastodon bot for forwarding messages.

## Usage

- [Create a telegram bot](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
- - Recieve telegram's access token
- [Create a mastodon bot](https://tinysubversions.com/notes/mastodon-bot/)
- - Give it the rights to write statuses
- - Save mastodon's access token
- Subscribe your telegram bot to channel(s) you need
- Install dependencies `pip install -r requirements.txt`
- Launch main.py and follow instructions
- Bot will start forwarding posts

### Limitations

- Only reposts plain text, images, and videos
- Image galleries are published as separate posts

# Телеміст

Телеграм/Мастодон бот, який дописи з тг в мастодон.

## Використання

- [Створіть бота в Телеграм](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
- - Отримайте токен доступу
- [Створіть бота в Мастодон](https://tinysubversions.com/notes/mastodon-bot/)
- - Дайте йому доступ до створення дописів
- - Збережіть токен доступу
- Підпишіть бота на потрібні канали в телеграмі
- Встановіть залежності `pip install -r requirements.txt`
- Відкрийте main.py і змініть видимість постів в `mastodon_visibility = "direct"`
- Запустіть скрипт і слідуйте інструкціям
- Бот почне постити нові дописи з каналу на який він підписаний

### Обмеження

- Підтримуються лише текст, світлини, та відео
- Галереї публікуються в окремих дописах

</details>

import html
import re, os
import time
from typing import List
import git
import requests
from io import BytesIO
from telegram import Update, MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, CallbackContext
from telegram.utils.helpers import mention_html, escape_markdown
from subprocess import Popen, PIPE

from tg_bot import (
    dispatcher,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    DEV_USERS,
    WHITELIST_USERS,
    StartTime
)
from tg_bot.__main__ import STATS, USER_INFO, TOKEN
from tg_bot.modules.sql import SESSION
from tg_bot.modules.helper_funcs.chat_status import user_admin, sudo_plus
from tg_bot.modules.helper_funcs.extraction import extract_user
import tg_bot.modules.sql.users_sql as sql
from tg_bot.modules.language import gs
from telegram import __version__ as ptbver, InlineKeyboardMarkup, InlineKeyboardButton
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time
import datetime
import platform
from platform import python_version
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigcallback


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

stats_str = '''
'''
@kigcmd(command='stats', can_disable=False)
@sudo_plus
def stats(update, context):
    db_size = SESSION.execute("SELECT pg_size_pretty(pg_database_size(current_database()))").scalar_one_or_none()
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    status = "*╒═══「 System statistics: 」*\n\n"
    status += "*• System Start time:* " + str(uptime) + "\n"
    uname = platform.uname()
    status += "*• System:* " + str(uname.system) + "\n"
    status += "*• Node name:* " + escape_markdown(str(uname.node)) + "\n"
    status += "*• Release:* " + escape_markdown(str(uname.release)) + "\n"
    status += "*• Machine:* " + escape_markdown(str(uname.machine)) + "\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "*• CPU:* " + str(cpu) + " %\n"
    status += "*• RAM:* " + str(mem[2]) + " %\n"
    status += "*• Storage:* " + str(disk[3]) + " %\n\n"
    status += "*• Python version:* " + python_version() + "\n"
    status += "*• python-telegram-bot:* " + str(ptbver) + "\n"
    status += "*• Uptime:* " + str(botuptime) + "\n"
    status += "*• Database size:* " + str(db_size) + "\n"
    kb = [
          [
           InlineKeyboardButton('Ping', callback_data='pingCB')
          ]
    ]
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    status += f"*• Commit*: `{sha[0:9]}`\n"
    try:
        update.effective_message.reply_text(status +
            "\n*Bot statistics*:\n"
            + "\n".join([mod.__stats__() for mod in STATS]) +
            "\n\n[⍙ GitHub](https://github.com/Dank-del/EnterpriseALRobot) | [⍚ GitLab](https://gitlab.com/Dank-del/EnterpriseALRobot)\n\n" +
            "╘══「 by [Dank-del](github.com/Dank-del) 」\n",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)
    except BaseException:
        update.effective_message.reply_text(
            (
                (
                    (
                        "\n*Bot statistics*:\n"
                        + "\n".join(mod.__stats__() for mod in STATS)
                    )
                    + "\n\n⍙ [GitHub](https://github.com/Dank-del/EnterpriseALRobot) | ⍚ [GitLab](https://gitlab.com/Dank-del/EnterpriseALRobot)\n\n"
                )
                + "╘══「 by [Dank-del](github.com/Dank-del) 」\n"
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb),
            disable_web_page_preview=True,
        )

@kigcmd(command='ping')
def ping(update: Update, _):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    message.edit_text(
        "*Pong!!!*\n`{}ms`".format(ping_time), parse_mode=ParseMode.MARKDOWN
    )


@kigcallback(pattern=r'^pingCB')
def pingCallback(update: Update, context: CallbackContext):
    query = update.callback_query
    start_time = time.time()
    requests.get('https://api.telegram.org')
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    query.answer('Pong! {}ms'.format(ping_time))


def get_help(chat):
    return gs(chat, "misc_help")



__mod_name__ = "Misc"

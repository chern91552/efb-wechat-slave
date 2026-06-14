# coding: utf-8
import base64
import io
import logging
import os
import subprocess
import json
from tempfile import NamedTemporaryFile
from typing import Dict, Any, TYPE_CHECKING, List, IO


from ehforwarderbot.types import MessageID
from .vendor.itchat import utils as itchat_utils

from .vendor import wxpy

if TYPE_CHECKING:
    from . import WeChatChannel

logger = logging.getLogger(__name__)

WC_EMOTICON_CONVERSION = {
    '[微笑]': '😃', '[Smile]': '😃',
    '[撇嘴]': '😖', '[Grimace]': '😖',
    '[色]': '😍', '[Drool]': '😍',
    '[发呆]': '😳', '[Scowl]': '😳',
    '[得意]': '😎', '[Chill]': '😎',
    '[流泪]': '😭', '[Sob]': '😭',
    '[害羞]': '☺️', '[Shy]': '☺️',
    '[闭嘴]': '🤐', '[Shutup]': '🤐',
    '[睡]': '😴', '[Sleep]': '😴',
    '[大哭]': '😣', '[Cry]': '😣',
    '[尴尬]': '😰', '[Awkward]': '😰',
    '[发怒]': '😡', '[Pout]': '😡',
    '[调皮]': '😜', '[Wink]': '😜',
    '[呲牙]': '😁', '[Grin]': '😁',
    '[惊讶]': '😱', '[Surprised]': '😱',
    '[难过]': '🙁', '[Frown]': '🙁',
    '[囧]': '☺️', '[Tension]': '☺️',
    '[抓狂]': '😫', '[Scream]': '😫',
    '[吐]': '🤢', '[Puke]': '🤢',
    '[偷笑]': '🙈', '[Chuckle]': '🙈',
    '[愉快]': '☺️', '[Joyful]': '☺️',
    '[白眼]': '🙄', '[Slight]': '🙄',
    '[傲慢]': '😕', '[Smug]': '😕',
    '[困]': '😪', '[Drowsy]': '😪',
    '[惊恐]': '😱', '[Panic]': '😱',
    '[流汗]': '😓', '[Sweat]': '😓',
    '[憨笑]': '😄', '[Laugh]': '😄',
    '[悠闲]': '😏', '[Loafer]': '😏',
    '[奋斗]': '💪', '[Strive]': '💪',
    '[咒骂]': '😤', '[Scold]': '😤',
    '[疑问]': '❓', '[Doubt]': '❓',
    '[嘘]': '🤐', '[Shhh]': '🤐',
    '[晕]': '😲', '[Dizzy]': '😲',
    '[衰]': '😳', '[BadLuck]': '😳',
    '[骷髅]': '💀', '[Skull]': '💀',
    '[敲打]': '👊', '[Hammer]': '👊',
    '[再见]': '🙋\u200d♂', '[Bye]': '🙋\u200d♂',
    '[擦汗]': '😥', '[Relief]': '😥',
    '[抠鼻]': '🤷\u200d♂', '[DigNose]': '🤷\u200d♂',
    '[鼓掌]': '👏', '[Clap]': '👏',
    '[坏笑]': '👻', '[Trick]': '👻',
    '[左哼哼]': '😾', '[Bah！L]': '😾',
    '[右哼哼]': '😾', '[Bah！R]': '😾',
    '[哈欠]': '😪', '[Yawn]': '😪',
    '[鄙视]': '😒', '[Lookdown]': '😒',
    '[委屈]': '😣', '[Wronged]': '😣',
    '[快哭了]': '😔', '[Puling]': '😔',
    '[阴险]': '😈', '[Sly]': '😈',
    '[亲亲]': '😘', '[Kiss]': '😘',
    '[可怜]': '😻', '[Whimper]': '😻',
    '[菜刀]': '🔪', '[Cleaver]': '🔪',
    '[西瓜]': '🍉', '[Melon]': '🍉',
    '[啤酒]': '🍺', '[Beer]': '🍺',
    '[咖啡]': '☕', '[Coffee]': '☕',
    '[猪头]': '🐷', '[Pig]': '🐷',
    '[玫瑰]': '🌹', '[Rose]': '🌹',
    '[凋谢]': '🥀', '[Wilt]': '🥀',
    '[嘴唇]': '💋', '[Lip]': '💋',
    '[爱心]': '❤️', '[Heart]': '❤️',
    '[心碎]': '💔', '[BrokenHeart]': '💔',
    '[蛋糕]': '🎂', '[Cake]': '🎂',
    '[炸弹]': '💣', '[Bomb]': '💣',
    '[便便]': '💩', '[Poop]': '💩',
    '[月亮]': '🌃', '[Moon]': '🌃',
    '[太阳]': '🌞', '[Sun]': '🌞',
    '[拥抱]': '🤗', '[Hug]': '🤗',
    '[强]': '👍', '[Strong]': '👍',
    '[弱]': '👎', '[Weak]': '👎',
    '[握手]': '🤝', '[Shake]': '🤝',
    '[胜利]': '✌️', '[Victory]': '✌️',
    '[抱拳]': '🙏', '[Salute]': '🙏',
    '[勾引]': '💁\u200d♂', '[Beckon]': '💁\u200d♂',
    '[拳头]': '👊', '[Fist]': '👊',
    '[OK]': '👌',
    '[跳跳]': '💃', '[Waddle]': '💃',
    '[发抖]': '🙇', '[Tremble]': '🙇',
    '[怄火]': '😡', '[Aaagh!]': '😡',
    '[转圈]': '🕺', '[Twirl]': '🕺',
    '[嘿哈]': '🤣', '[Hey]': '🤣',
    '[捂脸]': '🤦\u200d♂', '[Facepalm]': '🤦\u200d♂',
    '[奸笑]': '😜', '[Smirk]': '😜',
    '[机智]': '🤓', '[Smart]': '🤓',
    '[皱眉]': '😟', '[Concerned]': '😟',
    '[耶]': '✌️', '[Yeah!]': '✌️',
    '[红包]': '🧧', '[Packet]': '🧧',
    '[鸡]': '🐥', '[Chick]': '🐥',
    '[蜡烛]': '🕯️', '[Candle]': '🕯️',
    '[糗大了]': '😥',
    '[Thumbs Up]': '👍', '[Pleased]': '😊',
    '[Rich]': '🀅',
    '[Pup]': '🐶',
    '[吃瓜]': '🙄\u200d🍉',
    '[加油]': '💪\u200d😁',
    '[加油加油]': '💪\u200d😷',
    '[汗]': '😓',
    '[天啊]': '😱',
    '[Emm]': '🤔',
    '[社会社会]': '😏',
    '[旺柴]': '🐶\u200d😏',
    '[好的]': '😏\u200d👌',
    '[哇]': '🤩',
    '[打脸]': '😟\u200d🤚',
    '[破涕为笑]': '😂', '[破涕為笑]': '😂',
    '[苦涩]': '😭',
    '[翻白眼]': '🙄',
    '[裂开]': '🫠'
}


class ExperimentalFlagsManager:
    DEFAULT_VALUES = {
        'refresh_friends': False,
        'first_link_only': False,
        'max_quote_length': -1,
        'qr_reload': 'master_qr_code',
        'on_log_out': 'command',
        'imgcat_qr': False,
        'delete_on_edit': False,
        'app_shared_link_mode': 'ignore',
        'puid_logs': None,
        'send_stickers_and_gif_as_jpeg': False,
        'system_chats_to_include': ['filehelper'],
        'user_agent': None,
        'text_post_processing': True,
        'replace_emoticon': True,
    }

    def __init__(self, channel: 'WeChatChannel'):
        self.config: Dict[str, Any] = ExperimentalFlagsManager.DEFAULT_VALUES.copy()
        self.config.update(channel.config.get('flags', dict()) or dict())

    def __call__(self, flag_key: str) -> Any:
        if flag_key not in self.config:
            raise ValueError("%s is not a valid experimental flag" % flag_key)
        return self.config[flag_key]


def wechat_string_unescape(content: str, replace_emoticon: bool = True) -> str:
    """
    Unescape a WeChat HTML string.

    Args:
        content (str): String to be formatted

    Returns:
        str: Unescaped string.
    """
    if not content:
        return ""
    d: Dict[str, Any] = {"Content": content}
    itchat_utils.msg_formatter(d, "Content")
    if replace_emoticon:
        for i in WC_EMOTICON_CONVERSION:
            d['Content'] = d['Content'].replace(i, WC_EMOTICON_CONVERSION[i])
    return d['Content']


def generate_message_uid(messages: List[wxpy.SentMessage]) -> MessageID:
    return MessageID(json.dumps(
        [[message.chat.puid, message.id, message.local_id]
         for message in messages]
    ))


def message_id_to_dummy_message(message_uid: List[str], channel: 'WeChatChannel') -> wxpy.SentMessage:
    """
    Generate a wxpy.SentMessage object with minimum identifying information.
    This is generally used to recall messages using WXPY's API without the message object

    Args:
        message_uid: puid, id, local_id
        channel: the slave channel object that issued this message
    """
    puid, m_id, l_id = message_uid
    d = {
        'receiver': channel.chats.get_wxpy_chat_by_uid(puid),
        'id': m_id,
        'local_id': l_id
    }
    return wxpy.SentMessage(d)


def imgcat(file: io.BytesIO, filename: str) -> str:
    """
    Form a string to print in iTerm 2's ``imgcat`` format
    from a filename and a image file
    """

    def print_osc():
        if str(os.environ.get("TERM", "")).startswith("screen"):
            return "\x1bPtmux;\x1b\x1b]"
        else:
            return "\x1b]"

    def print_st():
        if str(os.environ.get("TERM", "")).startswith("screen"):
            return "\x07\x1b\\"
        else:
            return "\x07"

    res = print_osc()
    res += "1337;File=name="
    res += base64.b64encode(filename.encode()).decode()
    res += ";inline=1:"
    res += base64.b64encode(file.getvalue()).decode()
    res += print_st()
    return res


if os.name == "nt":
    # Workaround for Windows which cannot open the same file as "read" twice.
    # Using stdin/stdout pipe for IO with ffmpeg.
    # Said to be only working with a few encodings. It seems that Telegram GIF
    # (MP4, h264, soundless) luckily felt in that range.
    #
    # See: https://etm.1a23.studio/issues/90

    def gif_conversion(file: IO[bytes]) -> IO[bytes]:
        """Convert Telegram GIF to real GIF, the NT way."""
        file.seek(0)
        new_file_size = os.path.getsize(file.name)
        logger.debug("file_size: %.1fKB", new_file_size / 1024)
        if new_file_size > 1024 * 1024:
            # try to use gifsicle lossy compression
            compress_file = NamedTemporaryFile(suffix='.gif')
            subprocess.run(["gifsicle", "--resize-method=catrom", "--lossy=100", "-O2", "-o", compress_file.name, file.name], check=True)
            new_file_size = os.path.getsize(compress_file.name)
            if new_file_size > 1024 * 1024:
                scales = [512, 480, 400, 360, 300, 256, 250, 200, 150, 100]
                for scale in scales:
                    subprocess.run(["gifsicle", "--resize-method=catrom",  "--resize-fit", f"{scale}x{scale}", "--lossy=100", "-O2", "-o", compress_file.name, file.name], check=True)
                    new_file_size = os.path.getsize(compress_file.name)
                    logger.debug("new_file_size: %.1fKB after resize to %dx%d", new_file_size / 1024, scale, scale)
                    if new_file_size < 1024 * 1024:
                        break
            file.close()
            file = compress_file
        file.seek(0)
        return file

else:
    def gif_conversion(file: IO[bytes]) -> IO[bytes]:
        """Convert Telegram GIF to real GIF, the non-NT way."""
        file.seek(0)
        new_file_size = os.path.getsize(file.name)
        logger.debug("file_size: %.1fKB", new_file_size / 1024)
        if new_file_size > 1024 * 1024:
            # try to use gifsicle lossy compression
            compress_file = NamedTemporaryFile(suffix='.gif')
            subprocess.run(["gifsicle", "--resize-method=catrom", "--lossy=100", "-O2", "-o", compress_file.name, file.name], check=True)
            new_file_size = os.path.getsize(compress_file.name)
            if new_file_size > 1024 * 1024:
                scales = [512, 480, 400, 360, 300, 256, 250, 200, 150, 100]
                for scale in scales:
                    subprocess.run(["gifsicle", "--resize-method=catrom",  "--resize-fit", f"{scale}x{scale}", "--lossy=100", "-O2", "-o", compress_file.name, file.name], check=True)
                    new_file_size = os.path.getsize(compress_file.name)
                    logger.debug("new_file_size: %.1fKB after resize to %dx%d", new_file_size / 1024, scale, scale)
                    if new_file_size < 1024 * 1024:
                        break
            file.close()
            file = compress_file
        file.seek(0)
        return file

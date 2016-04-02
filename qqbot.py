# coding: UTF-8

import json
import random
import time
from collections import deque

from cqbot import CQBot, \
    RcvdPrivateMessage, SendPrivateMessage, \
    RcvdGroupMessage, SendGroupMessage, \
    RcvdDiscussMessage, SendDiscussMessage, \
    GroupMemberDecrease, GroupMemberIncrease


qqbot = CQBot(11231, 11232)


def match(text, keywords):
    for keyword in keywords:
        if keyword in text:
            return True
    return False


################
# log
################
@qqbot.handler
def log(message):
    print("↘", message)


def reply(message, text):
    reply_msg = None
    if isinstance(message, RcvdPrivateMessage):
        reply_msg = SendPrivateMessage(
            qq=message.qq,
            text=text,
            )
    if isinstance(message, RcvdGroupMessage):
        reply_msg = SendGroupMessage(
            group=message.group,
            text=text,
            )
    if isinstance(message, RcvdDiscussMessage):
        reply_msg = SendDiscussMessage(
            discuss=message.discuss,
            text=text,
            )
    if reply_msg:
        qqbot.send(reply_msg)
        print("↗", reply_msg)


################
# welcome
################
@qqbot.handler
def welcome(message):
    if isinstance(message, GroupMemberIncrease):
        welcome = SendGroupMessage(
            group=message.group,
            text="[CQ:at,qq={}] 欢迎来到 poi 用户讨论群。新人请发女装照一张。".format(
                message.operatedQQ)
            )
        qqbot.send(welcome)


################
# blacklist
################
BLACKLIST = []

with open('blacklist.json', 'r', encoding="utf-8") as f:
    BLACKLIST = json.loads(f.read())


@qqbot.handler
def blacklist(message):
    if not isinstance(message, (RcvdPrivateMessage,
                                RcvdGroupMessage,
                                RcvdDiscussMessage)):
        return True
    text = message.text.lower()
    return match(text, BLACKLIST)


################
# FAQ
################
FAQ_DEFAULT_INTERVAL = 60
FAQ = []


class FAQObject:
    def __init__(self, opts):
        self.keywords = opts["keywords"]
        self.whitelist = opts.get("whitelist", [])
        self.message = opts["message"]
        self.interval = opts.get("interval", FAQ_DEFAULT_INTERVAL)
        self.triggered = 0

with open('faq.json', 'r', encoding="utf-8") as f:
    jFAQ = json.loads(f.read())
    for jfaq in jFAQ:
        FAQ.append(FAQObject(jfaq))


@qqbot.handler
def faq(message):
    text = message.text.lower()
    now = time.time()
    for faq in FAQ:
        if not match(text, faq.keywords):
            continue
        if match(text, faq.whitelist):
            return True
        if (now - faq.triggered) < faq.interval:
            return True

        if isinstance(faq.message, list):
            send_text = random.choice(faq.message)
        else:
            send_text = faq.message

        faq.triggered = now
        reply(message, send_text)
        return True


################
# roll
################
ROLL_LOWER = 2
ROLL_UPPER = 7000


@qqbot.handler
def roll(message):
    texts = message.text.split()
    if not (len(texts) > 0 and texts[0] == '/roll'):
        return

    ranges = []
    for text in texts[1:5]:
        try:
            n = int(text)
        except:
            break
        if ROLL_LOWER <= n <= ROLL_UPPER:
            ranges.append(n)
        else:
            reply(message,
                  "[roll] 有效范围为 {} ~ {}".format(ROLL_LOWER, ROLL_UPPER))
            return True
    if len(ranges) == 0:
        ranges = [100]

    rolls = []
    for n in ranges:
        rolls.append("{}/{}".format(random.randint(1, n), n))
    roll_text = ", ".join(rolls)
    send_text = "[roll] [CQ:at,qq={}]: {}".format(message.qq, roll_text)

    reply(message, send_text)
    return True


################
# repeat
################
REPEAT_QUEUE_SIZE = 20
REPEAT_COUNT_MIN = 2
REPEAT_COUNT_MAX = 4
queue = deque()


class QueueMessage:
    def __init__(self, text):
        self.text = text
        self.count = 0
        self.repeated = False


@qqbot.handler
def repeat(message):
    text = message.text

    # Find & remove matched message from queue.
    msg = None
    for m in queue:
        if m.text == text:
            msg = m
            queue.remove(m)
            break

    # Increase message count
    if msg is None:
        msg = QueueMessage(text)
    msg.count += 1

    # Push message back to queue
    queue.appendleft(msg)
    if len(queue) > REPEAT_QUEUE_SIZE:
        queue.pop()

    # Repeat message
    if msg.repeated:
        return False
    if REPEAT_COUNT_MIN <= msg.count <= REPEAT_COUNT_MAX and \
            random.randint(1, REPEAT_COUNT_MAX - msg.count + 1) == 1:
        reply(message, msg.text)
        msg.repeated = True
        return True


if __name__ == '__main__':
    try:
        qqbot.start()
        print("QQBot is running...")
        input()
    except KeyboardInterrupt:
        pass

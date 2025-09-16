import json
import os
from datetime import datetime
from collections import defaultdict
from nonebot import on_message, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.log import logger

# 配置文件路径和日志文件路径 (与 textban.py 共用)
CONFIG_PATH = "/root/Lagrange.OneBot/nao/textban/config.json"
LOG_FILE_PATH = "/root/Lagrange.OneBot/nao/textban/noadpls.txt"
USER_VIOLATIONS_PATH = "/root/Lagrange.OneBot/nao/textban/user_violations.json"

# --- 全局变量 ---
# 监控的群组ID列表
monitored_groups = []
# 存储用户违规次数的字典 {group_id: {user_id: count}}
user_violations = defaultdict(lambda: defaultdict(int))

# --- 初始化加载 ---

def load_config():
    """从JSON文件加载配置"""
    global monitored_groups
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            monitored_groups = config.get("monitored_groups", [])
            logger.info(f"成功加载配置文件，监控群组: {monitored_groups}")
    except FileNotFoundError:
        logger.error(f"配置文件 {CONFIG_PATH} 未找到。")
    except json.JSONDecodeError:
        logger.error(f"配置文件 {CONFIG_PATH} 格式错误。")

def load_user_violations():
    """从文件加载用户违规记录"""
    global user_violations
    if os.path.exists(USER_VIOLATIONS_PATH):
        try:
            with open(USER_VIOLATIONS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for group_id, users in data.items():
                    for user_id, count in users.items():
                        user_violations[int(group_id)][int(user_id)] = count
                logger.info("成功加载用户违规记录。")
        except (json.JSONDecodeError, TypeError):
            logger.error("用户违规记录文件损坏，将创建新的记录。")
            user_violations = defaultdict(lambda: defaultdict(int))

def save_user_violations():
    """保存用户违规记录到文件"""
    with open(USER_VIOLATIONS_PATH, 'w', encoding='utf-8') as f:
        json.dump(user_violations, f, ensure_ascii=False, indent=4)

# 在机器人启动时执行初始化
@get_driver().on_startup
async def _():
    load_config()
    load_user_violations()

# --- 核心功能 ---

def log_action(group_id: int, user_name: str, message: str, result: str):
    """记录操作到日志文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{group_id}] [{user_name}] [{message}] [{result}]\n"
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"写入日志文件失败: {e}")

async def handle_violation(bot: Bot, event: GroupMessageEvent, reason: str):
    """处理检测到的违规行为"""
    group_id = event.group_id
    user_id = event.user_id
    user_name = event.sender.card or event.sender.nickname
    message_content = "推荐群聊卡片"

    # 排除管理员和群主
    try:
        user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        if user_info.get("role") in ["admin", "owner"]:
            logger.info(f"用户 {user_name}({user_id}) 是管理员/群主，已忽略。")
            return
    except Exception as e:
        logger.error(f"获取群成员信息失败: {e}, 可能是机器人权限不足或用户已退群。")
        # 如果无法获取信息，默认继续执行处理
        pass

    # 增加用户违规次数
    user_violations[group_id][user_id] += 1
    violation_count = user_violations[group_id][user_id]
    save_user_violations() # 实时保存记录

    action_result = ""
    action_description = ""

    try:
        # 第一次违规：撤回 + 警告
        if violation_count == 1:
            action_result = "撤回消息"
            action_description = "撤回"
            await bot.delete_msg(message_id=event.message_id)

        # 第二次违规：撤回 + 禁言30分钟 + 警告
        elif violation_count == 2:
            action_result = "撤回消息并禁言30分钟"
            action_description = "禁言30分钟"
            await bot.delete_msg(message_id=event.message_id)
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=30 * 60)

        # 第三次及以上违规：踢出群聊 + 警告
        else:
            action_result = "踢出群聊"
            action_description = "踢出群聊"
            try:
                await bot.delete_msg(message_id=event.message_id)
            except Exception as e:
                logger.warning(f"踢出前撤回消息失败: {e}")
            await bot.set_group_kick(group_id=group_id, user_id=user_id, reject_add_request=False)
            user_violations[group_id][user_id] = 0
            save_user_violations()

        # 发送统一的警告消息
        warning_msg = (
            f"{MessageSegment.at(user_id)} "
            f"你发送了违规内容({reason})，记录一次，"
            f"本次予以{action_description}，如果继续发送将被禁言或踢出群聊！"
        )
        await bot.send_group_msg(group_id=group_id, message=warning_msg)
        log_action(group_id, user_name, message_content, action_result)
        logger.info(f"处理违规: 群({group_id}) 用户({user_name}) 内容({message_content}) 结果({action_result})")

    except Exception as e:
        log_action(group_id, user_name, message_content, f"处理失败: {e}")
        logger.error(f"处理违规时发生错误: {e}")


# --- 消息响应器 ---
card_detector = on_message(priority=5, block=False)

@card_detector.handle()
async def handle_group_card(bot: Bot, event: GroupMessageEvent):
    # 检查是否为被监控的群
    if event.group_id not in monitored_groups:
        return

    # 遍历消息段，查找JSON类型的卡片
    for seg in event.message:
        if seg.type == "json":
            try:
                json_data = json.loads(seg.data.get("data", "{}"))
                app = json_data.get("app")
                if app in ["com.tencent.contact.lua", "com.tencent.troopsharecard"]:
                    await handle_violation(bot, event, "推荐群聊/联系人")
                    return # 处理后即返回
            except (json.JSONDecodeError, AttributeError):
                continue

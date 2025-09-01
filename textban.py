import json
import os
from datetime import datetime
from collections import defaultdict
from nonebot import on_message, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.log import logger

# 配置文件路径和日志文件路径
CONFIG_PATH = "/root/Lagrange.OneBot/nao/textban/config.json"
LOG_FILE_PATH = "/root/Lagrange.OneBot/nao/textban/noadpls.txt"
USER_VIOLATIONS_PATH = "/root/Lagrange.OneBot/nao/textban/user_violations.json"

# --- 全局变量 ---
# 监控的群组ID列表
monitored_groups = []
# 违禁词集合
forbidden_words = set()
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
            word_files = config.get("word_files", [])
            logger.info(f"成功加载配置文件，监控群组: {monitored_groups}")
            return word_files
    except FileNotFoundError:
        logger.error(f"配置文件 {CONFIG_PATH} 未找到，请在项目根目录创建。")
        return []
    except json.JSONDecodeError:
        logger.error(f"配置文件 {CONFIG_PATH} 格式错误。")
        return []

def load_forbidden_words(word_files):
    """从词库文件加载违禁词"""
    global forbidden_words
    forbidden_words.clear()
    for file_path in word_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        forbidden_words.add(word)
            logger.info(f"成功从 {file_path} 加载 {len(forbidden_words)} 个违禁词。")
        except FileNotFoundError:
            logger.error(f"词库文件 {file_path} 未找到。")
    if not forbidden_words:
        logger.warning("未加载任何违禁词，插件可能无法正常工作。")

def load_user_violations():
    """从文件加载用户违规记录"""
    global user_violations
    if os.path.exists(USER_VIOLATIONS_PATH):
        try:
            with open(USER_VIOLATIONS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将加载的数据转换为defaultdict
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
    word_files = load_config()
    if word_files:
        load_forbidden_words(word_files)
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

async def handle_violation(bot: Bot, event: GroupMessageEvent, detected_word: str):
    """处理检测到的违规行为"""
    group_id = event.group_id
    user_id = event.user_id
    user_name = event.sender.card or event.sender.nickname
    message_content = event.get_plaintext().strip()

    # 排除管理员和群主
    user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    if user_info.get("role") in ["admin", "owner"]:
        logger.info(f"用户 {user_name}({user_id}) 是管理员/群主，已忽略。")
        return

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
            # 踢出前先尝试撤回消息
            try:
                await bot.delete_msg(message_id=event.message_id)
            except Exception as e:
                logger.warning(f"踢出前撤回消息失败: {e}")
            await bot.set_group_kick(group_id=group_id, user_id=user_id, reject_add_request=False)
            # 踢出后重置该用户的违规次数
            user_violations[group_id][user_id] = 0
            save_user_violations()


        # 发送统一的警告消息
        warning_msg = (
            f"{MessageSegment.at(user_id)} "
            f"你发送了违规内容/推广内容(含'{detected_word}')，记录一次，"
            f"本次予以{action_description}，如果继续发送将被禁言或踢出群聊！"
        )
        await bot.send_group_msg(group_id=group_id, message=warning_msg)
        log_action(group_id, user_name, message_content, action_result)
        logger.info(f"处理违规: 群({group_id}) 用户({user_name}) 内容({message_content}) 结果({action_result})")

    except Exception as e:
        log_action(group_id, user_name, message_content, f"处理失败: {e}")
        logger.error(f"处理违规时发生错误: {e}")


# --- 消息响应器 ---
message_detector = on_message(priority=5, block=False)

@message_detector.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent):
    # 检查是否为被监控的群
    if event.group_id not in monitored_groups:
        return

    # 提取纯文本消息
    msg_text = event.get_plaintext().strip()
    if not msg_text:
        return

    # 检查消息中是否包含违禁词
    for word in forbidden_words:
        if word in msg_text:
            # 发现违禁词，立即处理并停止继续检查
            await handle_violation(bot, event, word)
            return
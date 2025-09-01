<div align="center">
  <a href="https://nonebot.dev/store"><img src="https://gastigado.cnies.org/d/project_nonebot_plugin_group_welcome/nbp_logo.png?sign=8bUAF9AtoEkfP4bTe2CrYhR0WP4X6ZbGKykZgAeEWL4=:0" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://gastigado.cnies.org/d/project_nonebot_plugin_group_welcome/NoneBotPlugin.svg?sign=ksAOYnkycNpxRKXh2FsfTooiMXafUh2YpuKdAXGZF5M=:0" width="240" alt="NoneBotPluginText"></p>

<h1>NoneBot Plugin Word Detector</h1>
</div>

一款为 NoneBot2 设计的群聊违禁词检测插件，能够根据用户违规次数实现递进式惩罚（警告撤回 -> 禁言 -> 踢出），并记录详细的操作日志。

## 效果图

<img src="https://gastigado.cnies.org/d/project_nonebot_plugin_group_welcome/PixPin_2025_09_01_18_15_05.png?sign=85TMwzimoUlY7A10RaTTQUYIf4uky-SJmFypuO-_oS8=:0" alt="效果图预览" style="zoom:50%;" />

## ✨ 功能

- **多词库支持**: 可通过配置文件同时加载多个本地词库文件。
- **分级惩罚机制**:
  - **第一次**检测到违规消息：撤回该消息并发送警告。
  - **第二次**检测到同一用户的违规消息：撤回消息并禁言该用户30分钟。
  - **第三次**检测到同一用户的违规消息：将该用户踢出群聊。
  - 踢出群聊后，检测次数重置。
- **持久化记录**: 用户违规次数会被记录在本地，即使机器人重启也不会丢失。
- **管理员豁免**: 自动忽略群主和管理员的消息，防止误判。
- **详细日志**: 所有检测和处理操作都会以Unix日志风格记录到本地文件 `noadpls.txt` 中，方便追溯。

## 🔧 配置

在使用前，请在您的 NoneBot 项目根目录下创建 `config.json` 文件，并根据您的实际情况进行配置。

**1. `config.json` 文件**

```json
{
    "monitored_groups": [
        123456789,
        987654321
    ],
    "word_files": [
        "D:\\path\\to\\your\\wordlist1.txt",
        "C:\\Users\\bot\\Desktop\\wordlist2.txt"
    ]
}
```

- `monitored_groups`: (必需) 一个包含群号的列表，插件将只在这些群聊中生效。
- `word_files`: (必需) 一个包含词库文件绝对路径的列表。

**2. 词库文件 (`.txt`)**

请根据 `config.json` 中填写的路径创建对应的 `.txt` 文件。每个违禁词占一行，例如：

```
违禁词1
违禁词2
广告内容
...
```

**3. 用户违规记录 (自动生成)**

插件会自动创建 `user_violations.json` 文件来存储用户的违规计数，您通常无需手动修改它。

## 安装

将 `textban.py` 放置在 NoneBot 项目的 `src/plugins` 目录下。修改第23行的图片显示和第34行的欢迎语即可。

违禁词库可以使用本人根据 [cleanse-speech](https://github.com/TelechaBot/cleanse-speech) 转换的词库 [清谈词库](https://github.com/excniesNIED/nao-chatbot/tree/main/nonebot-plugin-kawaii-robot/outer)：

- `advertisement`：默认中文广告词库
- `pornographic`：默认中文色情词库
- `politics`: 默认中文敏感词库
- `general`: 默认中文通用词库
- `netease`: 网易屏蔽词库

针对校园新生群、班级群等校园场景，可以使用本人整理的基于校园迎新群真实广告样本整理的广告检测词库 [campus-ad-detection-words](https://github.com/excniesNIED/campus-ad-detection-words)。

## 📖 使用

插件没有任何主动触发的命令。一旦配置完成并启动机器人，它将自动监控指定群聊中的消息。

当有用户（非管理员）发送的消息包含任意一个词库中的违禁词时，插件将根据其历史违规次数自动执行相应的惩罚操作。

## 📝 日志格式

所有操作都将被记录在 NoneBot 根目录下的 `noadpls.txt` 文件中。格式如下：

`[时间] [群号] [用户名] [消息内容] [处理结果]`

**示例:**

```log
[2025-09-01 10:12:20] [123456789] [张三] [这是一条广告消息] [撤回消息]
[2025-09-01 10:15:30] [123456789] [张三] [这是第二条广告] [撤回消息并禁言30分钟]
[2025-09-01 10:20:05] [987654321] [李四] [这是违规内容] [撤回消息]
```

## 💡 鸣谢

本插件站在了巨人的肩膀上，开发过程中吸收和借鉴了许多优秀项目的思想，感谢以下项目及其开发者：

- [nonebot-plugin-text-ban](https://github.com/zhongwen-4/nonebot-plugin-text-ban) 参考了功能实现
- [TelechaBot/cleanse-speech](https://github.com/TelechaBot/cleanse-speech) 参考了基础屏蔽机制和预定义词库
- [nonebot_plugin_admin](https://github.com/yzyyz1387/nonebot_plugin_admin)
- [nonebot-plugin-noadpls](https://github.com/LuoChu-NB2Dev/nonebot-plugin-noadpls)
- [zhenxun_bot](https://github.com/zhenxun-org/zhenxun_bot)

如果本插件无法满足您的全部需求，也推荐您了解和尝试上述优秀项目。

## 📄 开源许可

本插件使用 [MIT License](https://github.com/Melody-core/nonebot-plugin-word-detector/blob/main/LICENSE) 开源。
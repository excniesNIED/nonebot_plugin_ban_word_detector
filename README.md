<div align="center">
  <a href="https://nonebot.dev/store"><img src="https://gastigado.cnies.org/d/project_nonebot_plugin_group_welcome/nbp_logo.png?sign=8bUAF9AtoEkfP4bTe2CrYhR0WP4X6ZbGKykZgAeEWL4=:0" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://gastigado.cnies.org/d/project_nonebot_plugin_group_welcome/NoneBotPlugin.svg?sign=ksAOYnkycNpxRKXh2FsfTooiMXafUh2YpuKdAXGZF5M=:0" width="240" alt="NoneBotPluginText"></p>

<h1>NoneBot Plugin Word Detector</h1>
</div>

一款为 NoneBot2 设计的群聊违禁词检测插件，能够根据用户违规次数实现递进式惩罚（警告撤回 -> 禁言 -> 踢出），并记录详细的操作日志。

## ✨ 功能

- **多词库支持**: 可通过配置文件同时加载多个本地词库文件。
- **分级惩罚机制**:
  - **第一次**检测到违规消息：撤回该消息并发送警告。
  - **第二次**检测到同一用户的违规消息：撤回消息并禁言该用户30分钟。
  - **第三次**检测到同一用户的违规消息：将该用户踢出群聊。
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

## 使用方法

将 `textban.py` 放置在 NoneBot 项目的 `src/plugins` 目录下。修改第23行的图片显示和第34行的欢迎语即可。

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

## 📄 开源许可

本插件使用 [MIT License](https://github.com/Melody-core/nonebot-plugin-word-detector/blob/main/LICENSE) 开源。
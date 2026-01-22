# GLaDOS 自动签到  
使用教程：
1.点击 Star 和 Fork 这个项目

1.1 点击 Star
点个Star支持一下，非常感谢！

1.2 Fork 项目
步骤：
打开该项目的 GitHub 页面。
在页面右上角，点击 Fork 按钮。
选择你要 Fork 到的 GitHub 账户或组织。

2. 配置环境变量

2.1 在 GitHub 中设置 Secrets（环境变量）

为了让 CI/CD 流程使用敏感信息，我们使用 GitHub 的 Secrets 功能存储环境变量，这样可以安全地管理配置。

步骤：
打开你的 GitHub 仓库页面。

点击页面右上角的 Settings 按钮。

在左侧菜单栏找到 Secrets and variables，点击 Actions。

点击 New repository secret 按钮，添加以下 Secrets：

| 名称 | 说明 | 必填 |
|------|------|------|
| GLADOS_EMAIL_1 | 第一个账号的邮箱 | ✅ |
| GLADOS_COOKIE_1 | 第一个账号的 Cookie | ✅ |
| GLADOS_EMAIL_2 | 第二个账号的邮箱 | 可选 |
| GLADOS_COOKIE_2 | 第二个账号的 Cookie | 可选 |
| WECOM_WEBHOOK_URL | 企业微信机器人 Webhook 地址 | 可选 |
| HTTP_PROXY | HTTP 代理地址 | 可选 |
| HTTPS_PROXY | HTTPS 代理地址 | 可选 |

可以继续添加 GLADOS_EMAIL_3, GLADOS_COOKIE_3 等更多账号...

### 获取企业微信 Webhook

1. 在企业微信中创建群聊
2. 点击群设置 → 群机器人 → 添加机器人
3. 复制 Webhook 地址，格式如：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx`

注意：Secrets 一旦设置好后，GitHub Actions 会自动读取它们，无需手动在每次提交时修改代码

2.2 手动运行工作流，后续每天都会自动运行

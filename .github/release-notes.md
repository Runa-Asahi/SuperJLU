## SuperJLU v1.2.6

> 本版本是安全更新，建议所有用户尽快升级。

### 安全修复
- 修复本地 Web 界面接口缺少认证的问题（[GHSA-35pq-c9q2-4gv7](https://github.com/Runa-Asahi/SuperJLU/security/advisories/GHSA-35pq-c9q2-4gv7)）。此前同一设备上的其他程序可直接访问本地接口，读取成绩、课表和登录票据。现在接口需要随机令牌才能访问。v1.2.5 及以前的版本均受影响。
- 感谢 @Dramadan-wow 报告漏洞并提供补丁。

### 安全加固
- CI 在 main 上也运行测试，最低 Python 版本提到 3.10，新增 `SECURITY.md`（#136）。
- 验证码模板改用 JSON，去掉 pickle；系统钥匙串不可用时不再明文保存密码（#137）。

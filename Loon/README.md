# Loon

## China-AliDNS.lpx

将中国大陆域名交给阿里 DoH 解析的远程 Host 插件。数据源为 [felixonmars/dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list)。

在 Loon 配置中加入：

```ini
[Plugin]
https://raw.githubusercontent.com/miaoshououdezhi/Proxy/main/Loon/China-AliDNS.lpx,tag=国内域名阿里DoH,enabled=true
```

## 自动更新

GitHub Actions 每天 03:17（Asia/Taipei，UTC+8）抓取一次上游列表。生成结果通过格式和最小条目数校验后，仅在内容变化时由 `github-actions[bot]` 提交。也可以在 Actions 页面手动运行。

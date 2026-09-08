# Loon

## China-AliDNS.lpx

将中国大陆域名交给阿里 DoH 解析的远程 Host 插件。数据源为 `felixonmars/dnsmasq-china-list`，生成日期为 2026-09-08。

在 Loon 配置中加入：

```ini
[Plugin]
https://raw.githubusercontent.com/miaoshououdezhi/Proxy/main/Loon/China-AliDNS.lpx,tag=国内域名阿里DoH,enabled=true
```

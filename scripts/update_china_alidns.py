#!/usr/bin/env python3
"""Build a compact Loon Host plugin for common mainland China services."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

LINE_RE = re.compile(r"server=/([^/]+)/[^/]+")
DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}$")
DOH = "https://dns.alidns.com/dns-query"
MAX_OUTPUT_BYTES = 256 * 1024
MIN_UPSTREAM_DOMAINS = 100_000

# First-party and CDN roots for frequently used mainland services. Unknown
# domains safely continue through the main Cloudflare DoH configured in Loon.
LITE_DOMAINS = {
    # Alibaba / Ant / logistics
    "1688.com", "aliapp.org", "alibaba.com", "alibabacloud.com", "alicdn.com",
    "alipay.com", "alipayobjects.com", "aliyun.com", "aliyuncs.com", "amap.com",
    "cainiao.com", "dingtalk.com", "ele.me", "mmstat.com", "taobao.com",
    "taobaocdn.com", "tbcdn.com", "tmall.com", "tmall.hk", "ucweb.com", "youku.com",
    # Tencent / WeChat / QQ
    "gtimg.com", "idqqimg.com", "myapp.com", "myqcloud.com", "qcloud.com",
    "qcloudcdn.com", "qpic.com", "qq.com", "qqmail.com", "soso.com",
    "tencent.com", "tencent-cloud.com", "tencentmusic.com", "weixinbridge.com", "weiyun.com",
    # Baidu
    "baidu.com", "baidubce.com", "baidustatic.com", "bcebos.com", "bdimg.com",
    "bdstatic.com", "hao123.com", "tieba.com",
    # ByteDance / Douyin / Toutiao
    "amemv.com", "bytecdn.com", "byteimg.com", "bytedance.com", "bytednsdoc.com",
    "douyin.com", "douyincdn.com", "douyinpic.com", "douyinstatic.com", "feishu.net",
    "ixigua.com", "pstatp.com", "snssdk.com", "toutiao.com", "toutiaocdn.com",
    # Video / music / entertainment
    "acgvideo.com", "bilibili.com", "bilivideo.com", "douban.com", "douyu.com",
    "douyucdn.com", "hdslb.com", "huya.com", "huyacdn.com", "iqiyi.com",
    "kugou.com", "kuwo.com", "mgtv.com", "netease.com", "qiyi.com",
    "qiyipic.com", "xiami.com",
    # Shopping / local services / travel
    "360buyimg.com", "ctrip.com", "dianping.com", "didichuxing.com", "didiglobal.com",
    "jd.com", "jdcloud.com", "jdcdn.com", "jdpay.com", "kuaishou.com", "kwai.com",
    "meituan.com", "pinduoduo.com", "qunar.com", "suning.com", "vip.com",
    "xiaohongshu.com", "xhscdn.com", "yangkeduo.com",
    # Devices / cloud / software
    "360.com", "360safe.com", "antiy.com", "harmonyos.com", "honor.com", "huawei.com",
    "huaweicloud.com", "lenovo.com", "meizu.com", "mi.com", "miui.com", "oppo.com",
    "realme.com", "vivo.com", "xiaomi.com", "xiaomi.net", "wps.com",
    # Portals / community / email / recruitment
    "126.com", "127.net", "163.com", "51job.com", "58.com", "bosszhipin.com",
    "csdn.net", "gitee.com", "ifeng.com", "jianshu.com", "kanzhun.com", "oschina.net",
    "sina.com", "sogou.com", "sohu.com", "weibo.com", "zhihu.com", "zhipin.com",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_upstream(source: Path) -> tuple[set[str], str]:
    data = source.read_bytes()
    domains: set[str] = set()
    for line_number, raw_line in enumerate(data.decode("utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = LINE_RE.fullmatch(line)
        if not match:
            raise ValueError(f"unsupported source line {line_number}: {line!r}")
        domains.add(match.group(1).lower().rstrip("."))
    if len(domains) < MIN_UPSTREAM_DOMAINS:
        raise ValueError(f"upstream contains only {len(domains)} domains")
    return domains, hashlib.sha256(data).hexdigest()


def render(upstream: set[str], source_sha256: str) -> str:
    selected = sorted(LITE_DOMAINS & upstream)
    missing = sorted(LITE_DOMAINS - upstream)
    if len(selected) < 100:
        raise ValueError(f"only {len(selected)} Lite domains remain in upstream")
    if any(not DOMAIN_RE.fullmatch(domain) for domain in selected):
        raise ValueError("Lite domain list contains an invalid domain")
    lines = [
        "#!name = 国内常用域名阿里 DoH Lite",
        "#!desc = .cn 与常用中国服务使用阿里 DoH；其他域名使用主配置 DNS。",
        "#!author = miaoshououdezhi",
        "#!homepage = https://github.com/miaoshououdezhi/Proxy",
        "# Source: https://github.com/felixonmars/dnsmasq-china-list",
        f"# Source-SHA256: {source_sha256}",
        f"# Selected: {len(selected)} roots; skipped missing roots: {len(missing)}",
        "[Host]",
        f"*.cn = server:{DOH}",
    ]
    for domain in selected:
        lines.append(f"{domain} = server:{DOH}")
        lines.append(f"*.{domain} = server:{DOH}")
    output = "\n".join(lines) + "\n"
    size = len(output.encode("utf-8"))
    if size > MAX_OUTPUT_BYTES:
        raise ValueError(f"Lite output is too large: {size} bytes")
    return output


def main() -> None:
    args = parse_args()
    upstream, source_sha256 = load_upstream(args.source)
    output = render(upstream, source_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(output, encoding="utf-8")
    temporary.replace(args.output)
    print(f"generated {args.output}: {len(output.splitlines())} lines, {len(output.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()

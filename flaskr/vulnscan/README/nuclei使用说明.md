## 设置漏洞模板

修改`当前用户目录`下的`.config 配置文件

或者将本目录下的配置文件夹，修改后替换

**解决彩色颜色乱码**

1、[下载ANSICON --From Github](https://github.com/adoxa/ansicon/releases)

2、使用`cmd`控制台进入该文件夹

```bash
ansicon.exe -i
ansicon.exe -l
```

## 参数选项

```bash
-u， -target string使用核扫描的URL
-proxy-socks-url string  URL of the proxy socks server
-stats 显示正在运行的扫描的统计信息

-t， -templates value要运行的模板，支持使用目录创建单个模板和多个模板。
-tags value执行模板的标签
-tl 列出可用的模板
-w， -workflows value为核运行的工作流
```

## 使用示例

**工作流**

通过识别到的`web指纹`去进行漏洞扫描

```bash
nuclei -l urls.txt -w workflows/wordpress-workflow.yaml -stats -ra
```

工作流模板可叠加

**模板目录+标签**

```bash
nuclei -l urls.txt -tags apache -t default-logins/ -stats -ra
```

**漏洞严重程度**

```bash
nuclei -t cves/ -t vulnerabilities -severity critical,high -l urls.txt -stats -ra
```


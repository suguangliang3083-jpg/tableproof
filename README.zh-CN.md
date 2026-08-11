# TableProof 中文说明

TableProof 用来检查 CSV/TSV 合并是否符合预先声明的规则。

输入左右两张表和连接约束后，它会报告空键、重复键、实际基数、未匹配记录、各类连接的预计行数、可能的格式碰撞，以及已有结果表中的键多重集差异。命令行工具只使用 Python 标准库；Agent 负责调用工具和解释报告，不参与判定。

[English README](README.md) · [配置参考](docs/CONFIGURATION.md) · [报告结构](docs/REPORT_SCHEMA.md) · [Agent Skill 安装](docs/AGENT_SKILL.md)

当前版本为 [`v0.1.1`](https://github.com/suguangliang3083-jpg/tableproof/releases/tag/v0.1.1)，已发布到 [PyPI](https://pypi.org/project/tableproof/)。

## 常见问题

- 本应唯一的键出现重复，连接后行数增加；
- inner join 删除了没有匹配项的记录；
- 表格软件或导出流程把 `001` 改成 `1`；
- 结果同时少了记录、又多了别的记录，总行数却没有变化；
- 左右两侧都有重复键，形成 many-to-many 扩增。

## 安装

需要 Python 3.11 或更高版本。

```bash
python -m pip install tableproof
tableproof --version
```

从源码安装：

```bash
python -m pip install .
```

## 基本用法

生成带注释的配置：

```bash
tableproof init
```

执行配置中的全部检查：

```bash
tableproof check --config tableproof.toml
```

直接检查一次连接：

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many
```

检查已有结果表：

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many \
  --result merged.tsv --join-type left \
  --format json --output tableproof-report.json
```

## 先说明每行代表什么

检查前需要明确左右表每行对应的实体、键列及其顺序、预期连接关系，以及空键和未匹配记录的处理方式。

某列在当前文件里唯一，只能说明这份文件没有重复，不能说明它在采集、导出和分析流程中一直是稳定标识。例如，样本表中的 `sample_id` 可以唯一，而测量表中同一样本可以对应多条结果。

- `one-to-one`：两侧可用键都不能重复；
- `one-to-many`：左侧唯一，右侧可以重复；
- `many-to-one`：右侧唯一，左侧可以重复；
- `many-to-many`：两侧都可以重复，报告仍会列出扩增行数。

## 字符串比较

TableProof 按原始字符串比较键。它不会自动转数字、去空格、改大小写、去前导零、去重或改写源文件。`001`、`1`、`Sample-A`、`sample-a` 和尾部带空格的值是不同的键。

规范化警告表示某些未匹配值在假设的转换后会发生碰撞。这是一条核对线索，不是两条记录属于同一实体的证据。

## 报告和退出码

`--format text|json|markdown` 选择格式，`--output PATH` 写入文件。JSON 遵循固定的 Report Schema v1，不包含运行时间。

- `0`：通过当前失败阈值；
- `1`：数据违反策略，或在 `--fail-on warning` 下出现警告；
- `2`：命令、配置、编码、解析、I/O 或结果键推断错误。

报告默认只显示计数和截断后的 SHA-256 键样例。`--show-raw-keys` 或 `show_raw_keys = true` 会显示原值，不宜在未经审核的公共 CI 中开启。哈希也不等于匿名化，低熵标识符仍可能被猜测。

## GitHub Action

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v4
  - uses: suguangliang3083-jpg/tableproof@v1
    with:
      config: tableproof.toml
      fail-on: error
      report-dir: tableproof-reports
```

Action 不需要 API key 或写权限。它生成 annotations、job summary 和 JSON/Markdown 报告，并把输入和输出路径限制在 `GITHUB_WORKSPACE` 内。

## Agent Skill

Skill 位于 [`.agents/skills/table-proof`](.agents/skills/table-proof/SKILL.md)，采用 [Agent Skills 开放格式](https://agentskills.io/specification)，不绑定某一家模型：

- Codex 和当前 VS Code/GitHub Copilot 可以直接发现仓库中的 `.agents/skills/`；
- Claude Code 可把同一目录复制到 `.claude/skills/table-proof/`；
- claude.ai 可上传该目录的 ZIP；
- 其他兼容客户端按各自文档放置同一目录。

详见 [Agent Skill 安装与兼容范围](docs/AGENT_SKILL.md)。能读取 Skill 不代表运行环境一定具备 Python、文件访问和 `tableproof` CLI；文档会分别说明格式兼容与执行条件。

## v0.1 限制

- 只读取 UTF-8/UTF-8 BOM 的 CSV 与 TSV；
- 键频数保存在内存中，高基数大文件可能占用较多内存；
- 空键不参与匹配，即使两侧都为空；
- 结果检查比较连接键多重集，不核验每个非键字段的来源。

开发和采用情况记录在[项目证据台账](docs/CODEX_FOR_OSS_APPLICATION.md)中，只填写可公开核验的数字和链接。

## License

MIT

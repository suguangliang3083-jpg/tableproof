# TableProof 中文指南

TableProof 用来证明 CSV/TSV 合并是否保留了你认为应该保留的科研记录。它同时提供零运行时依赖的 Python CLI、GitHub Action 和 Agent Skill；数据结论完全由确定性程序给出，不调用 OpenAI API。

[English README](README.md) · [配置参考](docs/CONFIGURATION.md) · [报告 Schema v1](docs/REPORT_SCHEMA.md)

> 当前是 v0.1.0 初始版本。GitHub owner 已确认，PyPI 名称在 2026-08-11 查询时尚未被占用，但只有首次成功上传后才真正归属该账号；这里不声称已经获得 stars、下载量、采用案例或 OpenAI 项目资格。

## 它防什么错误

- 预期唯一的样本键重复，导致每条测量记录被成倍复制。
- inner join 没报错，却静默删除缺少匹配项的受试者。
- Excel 或导出步骤把 `001` 变成 `1`，导致标识符错配。
- 结果总行数看似正确，但恰好同时少一条、又多一条。
- 两侧都有重复键，形成 many-to-many 行数爆炸。

## 安装与快速使用

需要 Python 3.11 或更高版本。源码安装：

```bash
python -m pip install .
tableproof --version
```

生成带注释配置：

```bash
tableproof init
```

执行仓库级审计：

```bash
tableproof check --config tableproof.toml
```

执行单次检查：

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many
```

核验已经生成的结果表：

```bash
tableproof check \
  --left A.tsv --right B.tsv \
  --left-key sample_id --right-key sample_id \
  --expect one-to-many \
  --result merged.tsv --join-type left \
  --format json --output tableproof-report.json
```

## 先定义科学含义，再看唯一性

必须先回答：左表每行是什么实体？右表每行是什么实体？键来自哪个稳定命名空间？预期是一对一、一对多、多对一还是多对多？

某列在当前文件中“碰巧唯一”，不等于它是科学上稳定的主键。例如样本表中的 `sample_id` 可以唯一，而测量表中同一个样本应当出现多次。复合键按给定顺序比较。

- `one-to-one`：两侧都不允许重复可用键。
- `one-to-many`：左侧必须唯一，右侧允许重复；当前数据恰好 1:1 也满足约束。
- `many-to-one`：右侧必须唯一，左侧允许重复；当前数据恰好 1:1 也满足约束。
- `many-to-many`：两侧都可重复，但工具仍会警告行数扩增。

## 精确字符串原则

TableProof 始终按原始字符串比较键。它不会自动转数字、去空格、改大小写、去前导零、去重或改写原文件。`001`、`1`、`Sample-A`、`sample-a` 和尾部带空格的值都是不同的键。

工具会报告“如果执行某种规范化就可能碰撞”的线索，但这不是确认同一实体的证据。修复前必须核对上游标识符规则，并写入新文件、保留转换来源。

## 报告与退出码

`--format text|json|markdown` 控制格式，`--output PATH` 写入文件。JSON 遵循固定 Report Schema v1，并刻意不写运行时间；相同输入和配置会得到稳定内容。

- `0`：通过当前失败阈值。
- `1`：数据违反策略；或启用 `--fail-on warning` 后出现警告。
- `2`：配置、命令、编码、解析、I/O 或结果键推断错误。

默认只显示计数和截断后的 SHA-256 键样例。只有显式使用 `--show-raw-keys` 或配置 `show_raw_keys = true` 才显示原值。即使哈希也不等于完全匿名，低熵标识符仍可能被猜测。

## GitHub Action

仓库发布并维护 `v1` 标签后：

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

Action 不需要 API key 或写权限，会生成 annotations、job summary，以及 JSON/Markdown 报告路径。它会强制使用哈希样例（即使 PR 修改了 `show_raw_keys`），并把全部路径限制在 `GITHUB_WORKSPACE` 内。

## Agent Skill

Skill 位于 [`.agents/skills/table-proof`](.agents/skills/table-proof/SKILL.md)。它要求 Agent 先确认行实体、键和关系，再调用 CLI；默认不改原始数据，修复建议与实际修改分开。

## v0.1 边界

- 只支持 UTF-8/UTF-8 BOM 的 CSV 与 TSV。
- 内存中保存键频数；高基数超大文件可能占用较多内存，流式/落盘方案列入路线图。
- 空键不参与匹配，即使两侧都为空。
- 结果核验比较连接键多重集；它不能证明所有非键字段都来自正确源行。

## 维护与申请原则

项目必须先真实解决数据完整性问题，再谈申请。使用 [Codex for OSS 证据台账](docs/CODEX_FOR_OSS_APPLICATION.md) 只记录当时可公开核验的仓库、角色、stars、下载量、采用、发布与 issue；不得刷星、互换 stars 或虚构案例。项目为滚动、选择性审核，完成仓库不保证获批。提交前重新核对[官方说明](https://developers.openai.com/community/codex-for-oss)和[条款](https://learn.chatgpt.com/docs/codex-for-oss-terms)。

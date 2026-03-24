# 三钱起卦法（Python 版）

基于原 React 项目重构的 FastAPI + Jinja2 版本，保留了三钱起卦核心算法、64 卦解释与历史记录。

## 功能

- 六次抛掷三枚硬币生成爻象
- 自动推导本卦与变卦
- 展示总评、事业、情感、曾老指引、动爻信息
- SQLite 本地历史记录（查看/删除/清空）

## 运行

```bash
cd python_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

打开：`http://127.0.0.1:8000`

## 数据说明

- 64 卦数据文件：`python_app/data/hexagrams.json`
- 数据导出脚本：`scripts/export_hexagrams.mjs`
- 若原项目 `constants.ts` 更新，可重新执行：

```bash
node scripts/export_hexagrams.mjs
```

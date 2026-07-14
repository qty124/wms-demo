# 📚 BookWMS 仓储管理系统

> 一个面向**图书仓储**场景的演示型管理系统，适合作为课程作业 / 毕业设计 / 个人作品展示。
> 包含商品管理、入库 / 出库、库存预警、出入库流水等核心功能。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Demo-orange)

## ✨ 功能一览

| 模块 | 描述 |
|------|------|
| 📊 仪表盘 | 4 张统计卡片 + 近期流水 + 分类分布 + 库存预警 |
| 📖 商品管理 | 增 / 删 / 改 / 查，支持搜索（书名/作者/ISBN）+ 分类筛选 |
| 📥 入库 | 选择商品 + 数量，自动累加库存并写流水 |
| 📤 出库 | 防负库存校验，自动扣减库存并写流水 |
| 📜 流水历史 | 200 条记录按时间倒序展示 |
| ⚠️ 库存预警 | 阈值可配置，首页侧栏实时显示 |
| 🎨 UI | Bootstrap 5.3 + Bootstrap Icons，响应式设计 |

## 🛠 技术栈

- **后端**：Python 3.10 + Flask 3.0 + Flask-SQLAlchemy 3.1
- **数据库**：SQLite（单文件，零配置）
- **前端**：Bootstrap 5.3 + Bootstrap Icons + Jinja2 模板
- **部署**：Gunicorn + Render 免费版 / 任意支持 Python 的 PaaS
- **代码托管**：GitHub

## 📁 目录结构

```
仓储管理系统/
├── app.py              # Flask 主程序（路由 + 工厂函数 + 示例数据）
├── models.py           # SQLAlchemy 数据模型（Product / Transaction）
├── requirements.txt    # Python 依赖
├── Procfile            # Render / Heroku 启动声明
├── render.yaml         # Render IaC 配置
├── .gitignore
├── instance/wms.db     # SQLite 数据库（首次运行自动生成）
├── templates/          # Jinja2 模板
│   ├── base.html
│   ├── dashboard.html
│   ├── products.html
│   ├── product_form.html
│   ├── stock_in.html   # 入库 + 出库共用
│   ├── transactions.html
│   ├── about.html
│   └── error.html
└── static/css/style.css
```

## 🚀 本地运行

### 1. 克隆仓库
```bash
git clone https://github.com/qty124/wms-demo.git
cd wms-demo
```

### 2. 创建虚拟环境并安装依赖
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

> ⚠️ **网络提示**：如果遇到 `ValueError: check_hostname requires server_hostname`，
> 通常是系统代理与 pip SSL 验证冲突。临时绕过：
> ```powershell
> $env:NO_PROXY="*"
> .\venv\Scripts\python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
> ```

### 3. 启动应用
```bash
.\.venv\Scripts\python app.py
# 浏览器访问 http://127.0.0.1:5000
```

首次启动会自动建表 + 预填 12 本图书 + 7 条流水，开箱即用。

## 🌐 部署到 Render（推荐，免费）

1. 把代码 push 到你的 GitHub 仓库（参考下方"部署到 GitHub"）
2. 登录 [render.com](https://render.com)，点 **New** → **Blueprint**
3. 连接 GitHub 仓库 `qty124/wms-demo`
4. Render 会自动读取 `render.yaml` 完成部署
5. 几分钟后即可获得一个 `https://bookwms.onrender.com` 的在线链接

> 💡 免费版 15 分钟无访问会休眠，下次访问需等待 ~30 秒冷启动。

### 替代部署平台
- **Railway.app** - 同样支持 GitHub 集成，每月 $5 免费额度
- **Vercel** - 仅适合改造为 Serverless（需把 SQLite 换 Vercel Postgres）
- **GitHub Pages** - ❌ 不支持后端，仅纯静态站

## 📊 数据模型

### products（商品表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| isbn | String(20) UNIQUE | ISBN 号 |
| title | String(120) | 书名 |
| author | String(60) | 作者 |
| publisher | String(60) | 出版社 |
| category | String(30) | 分类 |
| stock | Integer | 当前库存 |
| cost | Float | 进价 |
| price | Float | 售价 |
| low_stock_threshold | Integer | 库存预警阈值 |
| location | String(30) | 货架位置，如 A-01-03 |
| created_at | DateTime | 创建时间 |

### transactions（出入库流水表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增主键 |
| product_id | Integer FK | 关联商品 |
| type | String(10) | "in" 入库 / "out" 出库 |
| quantity | Integer | 数量（正整数） |
| note | String(200) | 备注 |
| operator | String(30) | 操作人 |
| created_at | DateTime | 操作时间 |

## 🎯 截图预览

打开应用后默认看到仪表盘：

```
┌────────────────────────────────────────────────┐
│  仪表盘                       [入库] [出库]    │
├────────────────────────────────────────────────┤
│  [商品总数 12]  [总库存 178]  [价值 ¥12k]  [预警 3] │
├────────────────────────────────────────────────┤
│  近期出入库                │  库存预警           │
│  ┌─────────────────┐      │  ┌──────────┐    │
│  │ +10 新书到货   │      │  │ 人月神话  0  │    │
│  │  -3 客户订单   │      │  │ 黑客与画家 5/8│   │
│  │ ...            │      │  │ TCP/IP  8/10  │   │
│  └─────────────────┘      │  └──────────┘    │
│  分类库存分布              │                   │
└────────────────────────────────────────────────┘
```

## 📝 学习要点

如果你是网络工程 / 计算机专业学生，可以从本项目学到：

1. **Flask 工厂模式** - `create_app()` 模式解耦配置与运行
2. **SQLAlchemy ORM** - 用 Python 类映射数据库表，避免裸 SQL
3. **Jinja2 模板继承** - `base.html` + `extends` + `block`
4. **Bootstrap 5** - 快速搭建现代化响应式 UI
5. **CRUD 设计** - 增删改查的路由设计与表单处理
6. **数据库事务** - 入库/出库时同步更新商品和流水（一致性）
7. **免费云部署** - Render / Railway 部署 Flask 应用的完整流程

## 📄 License

MIT License - 自由使用、修改、分发

## 👩‍💻 作者

- GitHub: [@qty124](https://github.com/qty124)
- 演示场景：图书仓储 / 课程设计

---

⭐ 如果这个项目对你有帮助，欢迎在 GitHub 上点个 Star！

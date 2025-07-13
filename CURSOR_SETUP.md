# MyRid 项目 - Cursor Python 环境配置指南

## 📋 环境状态

✅ **Python 虚拟环境已就绪！**

- **环境名称**: `myrid-env`
- **Python 版本**: 3.9.23
- **环境路径**: `/Users/duwei/anaconda3/envs/myrid-env/bin/python`

## 🚀 快速配置步骤

### 1. 在 Cursor 中选择 Python 解释器

1. 按 `Cmd+Shift+P` 打开命令面板
2. 输入 `Python: Select Interpreter`
3. 选择 `/Users/duwei/anaconda3/envs/myrid-env/bin/python`

### 2. 验证配置

按 `Cmd+Shift+P`，输入 `Python: Run Python File in Terminal`，运行以下测试代码：

```python
# 测试环境
import sys
print(f"Python 版本: {sys.version}")
print(f"Python 路径: {sys.executable}")

# 测试核心依赖
try:
    import shapely, pyproj, networkx, numpy, pandas, psycopg2
    print("✅ 所有核心依赖包已安装!")
except ImportError as e:
    print(f"❌ 依赖包问题: {e}")
```

## 📦 已安装的核心依赖

| 包名          | 版本   | 功能            |
| ------------- | ------ | --------------- |
| shapely       | 2.0.7  | 几何操作        |
| pyproj        | 3.6.1  | 坐标转换        |
| networkx      | 3.2.1  | 图论算法        |
| numpy         | 2.0.2  | 数值计算        |
| pandas        | 2.3.1  | 数据处理        |
| psycopg2      | 2.9.10 | PostgreSQL 连接 |
| geographiclib | 2.0    | 地理计算        |

## 🛠️ 开发工具

| 工具   | 版本   | 用途       |
| ------ | ------ | ---------- |
| pylint | 3.3.7  | 代码检查   |
| black  | 25.1.0 | 代码格式化 |
| pytest | 8.4.1  | 单元测试   |

## 📝 VSCode/Cursor 配置文件

项目已自动创建 `.vscode/settings.json`，包含：

```json
{
  "python.defaultInterpreterPath": "/Users/duwei/anaconda3/envs/myrid-env/bin/python",
  "python.analysis.extraPaths": ["./lib", "./src", "./ui"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true
}
```

## 🎯 使用建议

### 1. 智能提示

- Cursor 会自动提供项目内模块的智能提示
- 支持 `lib/`, `src/`, `ui/` 目录下的模块导入

### 2. 代码格式化

- 保存时自动格式化（已启用）
- 手动格式化：`Cmd+Shift+P` → `Format Document`

### 3. 代码检查

- 实时语法检查和错误提示
- pylint 集成，符合项目规范

### 4. 调试支持

- 设置断点进行调试
- 支持 QGIS 插件开发调试

## ⚡ 常用快捷键

| 功能       | 快捷键        |
| ---------- | ------------- |
| 运行文件   | `Ctrl+F5`     |
| 调试       | `F5`          |
| 格式化代码 | `Shift+Alt+F` |
| 查找引用   | `Shift+F12`   |
| 转到定义   | `F12`         |

## 🔧 故障排除

### 问题 1：导入错误

如果遇到 QGIS 相关的导入错误，这是正常的，因为 QGIS 模块只在 QGIS 环境中可用。

### 问题 2：模块找不到

确保在 `.vscode/settings.json` 中正确配置了 `python.analysis.extraPaths`。

### 问题 3：环境切换

如需重新选择解释器：
`Cmd+Shift+P` → `Python: Select Interpreter` → 选择 myrid-env 环境

## 📚 项目结构说明

```
myrid/
├── .vscode/settings.json    # Cursor配置
├── requirements.txt         # Python依赖
├── pyproject.toml          # 项目配置
├── activate_env.sh         # 环境激活脚本
├── lib/                    # 第三方库
├── src/                    # 核心源码
├── ui/                     # 界面文件
└── config/                 # 配置文件
```

## 🎉 完成！

现在您可以在 Cursor 中愉快地开发 MyRid 项目了！环境配置已完成，支持智能提示、代码检查、格式化等现代 Python 开发功能。

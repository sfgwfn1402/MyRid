#!/bin/bash

# MyRid项目环境激活脚本
# 用法: source activate_env.sh

echo "🚀 正在激活MyRid开发环境..."

# 激活conda环境
conda activate myrid-env

# 验证Python版本
echo "✅ Python版本: $(python --version)"

# 验证关键包
echo "📦 检查关键依赖包..."
python -c "
try:
    import shapely
    print('✅ shapely:', shapely.__version__)
except ImportError:
    print('❌ shapely 未安装')

try:
    import pyproj
    print('✅ pyproj:', pyproj.__version__)
except ImportError:
    print('❌ pyproj 未安装')

try:
    import networkx
    print('✅ networkx:', networkx.__version__)
except ImportError:
    print('❌ networkx 未安装')

try:
    import psycopg2
    print('✅ psycopg2:', psycopg2.__version__)
except ImportError:
    print('❌ psycopg2 未安装')

try:
    import numpy
    print('✅ numpy:', numpy.__version__)
except ImportError:
    print('❌ numpy 未安装')

try:
    import pandas
    print('✅ pandas:', pandas.__version__)
except ImportError:
    print('❌ pandas 未安装')
"

echo ""
echo "🎯 MyRid开发环境已就绪！"
echo "📁 项目目录: $(pwd)"
echo "🐍 Python路径: $(which python)"
echo "📝 在Cursor中按Cmd+Shift+P，输入'Python: Select Interpreter'选择解释器"
echo ""
echo "💡 常用命令："
echo "   - 运行测试: pytest"
echo "   - 代码格式化: black ."
echo "   - 代码检查: pylint src/"
echo "   - 退出环境: conda deactivate" 